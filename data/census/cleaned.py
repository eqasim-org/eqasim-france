from tqdm import tqdm
import pandas as pd
import numpy as np
import data.hts.hts as hts

"""
This stage cleans the French population census:
  - Assign new unique integer IDs to households and persons
  - Clean up spatial information and sociodemographic attributes
"""

def configure(context):
    context.stage("data.census.raw")
    context.stage("data.spatial.codes")

    context.config("with_motorcycles", False)

    if context.config("use_urban_type", False):
        context.stage("data.spatial.urban_type")

def execute(context):
    df = context.stage("data.census.raw")

    # Construct household IDs for persons with NUMMI != Z
    df_household_ids = df[["CANTVILLE", "NUMMI"]]
    df_household_ids = df_household_ids[df_household_ids["NUMMI"] != "Z"]
    df_household_ids["temporary"] = df_household_ids["CANTVILLE"] + df_household_ids["NUMMI"]
    df_household_ids = df_household_ids.drop_duplicates("temporary")
    df_household_ids["household_id"] = np.arange(len(df_household_ids))
    df = pd.merge(df, df_household_ids, on = ["CANTVILLE", "NUMMI"], how = "left")

    # Fill up undefined household ids (those where NUMMI == Z)
    f = np.isnan(df["household_id"])
    df.loc[f, "household_id"] = np.arange(np.count_nonzero(f)) + df["household_id"].max() + 1
    df["household_id"] = df["household_id"].astype(int)

    # Put person IDs
    df["person_id"] = np.arange(len(df))

    # Sorting
    df = df.sort_values(by = ["household_id", "person_id"])

    # Spatial information
    df["departement_id"] = df["DEPT"].astype("category")

    df["commune_id"] = df["IRIS"].str[:5]
    f_undefined = df["commune_id"].str.contains("Z")
    df.loc[f_undefined, "commune_id"] = "undefined"
    df["commune_id"] = df["commune_id"].astype("category")

    df["iris_id"] = df["IRIS"]
    f_undefined = df["iris_id"].str.contains("Z") | df["iris_id"].str.contains("X")
    df.loc[f_undefined, "iris_id"] = "undefined"
    df["iris_id"] = df["iris_id"].astype("category")

    # Age
    df["age"] = df["AGED"].apply(lambda x: "0" if x == "000" else x.lstrip("0")).astype(int)

    # Clean COUPLE
    df["couple"] = df["COUPLE"] == "1"

    # Clean TRANS
    df["commute_mode"] = None
    df.loc[df["TRANS"] == "1", "commute_mode"] = np.nan
    df.loc[df["TRANS"] == "2", "commute_mode"] = "walk"
    df.loc[df["TRANS"] == "3", "commute_mode"] = "bike"
    df.loc[df["TRANS"] == "4", "commute_mode"] = "motorcycle"
    df.loc[df["TRANS"] == "5", "commute_mode"] = "car"
    df.loc[df["TRANS"] == "6", "commute_mode"] = "pt"
    df.loc[df["TRANS"] == "Z", "commute_mode"] = np.nan
    df["commute_mode"] = df["commute_mode"].astype("category")

    # Weight
    df["weight"] = df["IPONDI"].astype(float)

    # Clean SEXE
    df.loc[df["SEXE"] == "1", "sex"] = "male"
    df.loc[df["SEXE"] == "2", "sex"] = "female"
    df["sex"] = df["sex"].astype("category")

    # Clean professional occupation
    df["professional_activity"] = df["TACT"].replace({
        "11": "full_time_worker",
        "12": "unemployed",
        "21": "retired",
        "22": "student",
        "23": "under14",
        "24": "homemaker",
        "25": "other",
    })
    # Flag part-time workers.
    df.loc[(df["TACT"] == "11") & (df["TP"] == "2"), "professional_activity"] = "part_time_worker"

    # Clean employment
    df["employed"] = df["TACT"] == "11"

    # Studies
    # Note that some persons can have "professional_activity" != "student" and "studies" == True
    # (interns, apprenticeship, unemployed with trainings).
    # They represent about 13% of all "studies" == True.
    # Note that some persons can have "professional_activity" == "student" and "studies" == False
    # (probably representing at home education).
    df["studies"] = df["ETUD"] == "1"

    # Number of vehicles
    df["number_of_cars"] = df["VOIT"].apply(
        lambda x: str(x).replace("Z", "0").replace("X", "0")
    ).astype(int)

    df["number_of_motorcycles"] = df["DEROU"].apply(
        lambda x: str(x).replace("U", "0").replace("Z", "0").replace("X", "0")
    ).astype(int)
    # DEROU is often not known, if commute by motorcycle, at least one motorcycle in the household
    df["number_of_motorcycles"] += ((df["number_of_motorcycles"] == 0) & (df["commute_mode"] == "motorcycle")).astype(int)
    df["number_of_vehicles"] = df["number_of_cars"] + df["number_of_motorcycles"]

    # Force the use of motorcycle if commute by motorcycle
    df["use_motorcycle"] = False
    if context.config("with_motorcycles"):
        df.loc[(df["commute_mode"] == "motorcycle"), "use_motorcycle"] = True

    # Household size
    df_size = df[["household_id"]].groupby("household_id").size().reset_index(name = "household_size")
    df = pd.merge(df, df_size)

    # Socioprofessional category

    # Starting with RP 2022, INSEE does not provide the variable CS8 anymore,
    # which corresponded to the socioprofessional category in 8 classes (PCS2003).
    # Instead, the PCS2020 is provided now, in 6 classes. The first 6 classes are
    # equivalent, but class 7 (retired people) and class 8 (others) is removed.

    # there are two ways: we can backfit the data here (currently the case) so that
    # the matching with the older HTS later in the pipeline stays coherent

    # or we construct a new matching variable both here and in the surveys, which would
    # be the preferred way but is a TODO for now

    df["socioprofessional_class"] = df["GS"].replace({ "Z": "8" }).astype(int)

    # reconstruct retired people from "professional_activity"
    df.loc[df["professional_activity"] == "retired", "socioprofessional_class"] = 7

    # TODO: in the future matching variable, would be good to treat students / pupils separately

    # Consumption units
    df = pd.merge(df, hts.calculate_consumption_units(df), on = "household_id")

    df = df[[
        "person_id", "household_id", "weight",
        "iris_id", "commune_id", "departement_id",
        "age", "sex", "couple",
        "professional_activity",
        "commute_mode", "employed", "studies",
        "number_of_cars", "number_of_motorcycles", "number_of_vehicles", "use_motorcycle",
        "household_size", "consumption_units", "socioprofessional_class"
    ]]

    if context.config("use_urban_type"):
        df_urban_type = context.stage("data.spatial.urban_type")[[
            "commune_id", "urban_type"
        ]]

        # Impute urban type
        df = pd.merge(df, df_urban_type, on = "commune_id", how = "left")
        df.loc[df["commune_id"] == "undefined", "urban_type"] = "none"
        df["commune_id"] = df["commune_id"].astype("category")
        assert ~np.any(df["urban_type"].isna())

    return df
