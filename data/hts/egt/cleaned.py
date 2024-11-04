from tqdm import tqdm
import pandas as pd
import numpy as np
import data.hts.hts as hts

"""
This stage cleans the regional HTS.
"""

def configure(context):
    context.stage("data.hts.egt.raw")

    if context.config("use_urban_type", False):
        context.stage("data.spatial.urban_type")

INCOME_CLASS_BOUNDS = [800, 1200, 1600, 2000, 2400, 3000, 3500, 4500, 5500, 1e6]

PURPOSE_MAP = {
    1 : "home",
    2 : "work",
    3 : "work",
    4 : "education",
    5 : "shop",
    6 : "other",
    7 : "other",
    8 : "leisure"
    # 9 : "other" # default
}

MODES_MAP = {
    1 : "pt",
    2 : "car",
    3 : "car_passenger",
    4 : "car",
    5 : "bike",
    #6 : "pt", # default (other)
    7 : "walk"
}

def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.egt.raw")

    # Make copies
    df_households = pd.DataFrame(df_households, copy = True)
    df_persons = pd.DataFrame(df_persons, copy = True)
    df_trips = pd.DataFrame(df_trips, copy = True)

    # Transform original IDs to integer (they are hierarchichal)
    df_households["egt_household_id"] = df_households["NQUEST"].astype(int)
    df_persons["egt_person_id"] = df_persons["NP"].astype(int)
    df_persons["egt_household_id"] = df_persons["NQUEST"].astype(int)
    df_trips["egt_person_id"] = df_trips["NP"].astype(int)
    df_trips["egt_household_id"] = df_trips["NQUEST"].astype(int)
    df_trips["egt_trip_id"] = df_trips["ND"].astype(int)

    # Construct new IDs for households, persons and trips (which are unique globally)
    df_households["household_id"] = np.arange(len(df_households))

    df_persons = pd.merge(
        df_persons, df_households[["egt_household_id", "household_id"]],
        on = "egt_household_id"
    )
    df_persons["person_id"] = np.arange(len(df_persons))

    df_trips = pd.merge(
        df_trips, df_persons[["egt_person_id", "egt_household_id", "person_id", "household_id"]],
        on = ["egt_person_id", "egt_household_id"]
    )
    df_trips["trip_id"] = np.arange(len(df_trips))

    # Trip flags
    df_trips = hts.compute_first_last(df_trips)

    # Weight
    df_persons["person_weight"] = df_persons["POIDSP"].astype(float)
    df_households["household_weight"] = df_households["POIDSM"].astype(float)

    # Clean age
    df_persons["age"] = df_persons["AGE"].astype(int)

    # Clean sex
    df_persons.loc[df_persons["SEXE"] == 1, "sex"] = "male"
    df_persons.loc[df_persons["SEXE"] == 2, "sex"] = "female"
    df_persons["sex"] = df_persons["sex"].astype("category")

    # Household size
    df_households["household_size"] = df_households["MNP"].astype(int)

    # Clean departement
    df_persons["departement_id"] = df_persons["RESDEP"].astype(str).astype("category")
    df_households["departement_id"] = df_households["RESDEP"].astype(str).astype("category")
    df_trips["origin_departement_id"] = df_trips["ORDEP"].astype(str).astype("category")
    df_trips["destination_departement_id"] = df_trips["DESTDEP"].astype(str).astype("category")

    # Clean employment
    df_persons["employed"] = df_persons["OCCP"].isin([1.0, 2.0])

    # Studies
    df_persons["studies"] = df_persons["OCCP"].isin([3.0, 4.0, 5.0])

    # Number of vehicles
    df_households["number_of_vehicles"] = df_households["NB_2RM"] + df_households["NB_VD"]
    df_households["number_of_vehicles"] = df_households["number_of_vehicles"].astype(int)
    df_households["number_of_bikes"] = df_households["NB_VELO"].astype(int)

    # License
    df_persons["has_license"] = (df_persons["PERMVP"] == 1) | (df_persons["PERM2RM"] == 1)

    # Has subscription
    df_persons["has_pt_subscription"] = df_persons["ABONTC"] > 1

    # Household income
    df_households["income_class"] = df_households["REVENU"] - 1
    df_households.loc[df_households["income_class"].isin([10.0, 11.0, np.nan]), "income_class"] = -1
    df_households["income_class"] = df_households["income_class"].astype(int)

    # Impute urban type
    if context.config("use_urban_type"):
        df_urban_type = context.stage("data.spatial.urban_type")[[
            "commune_id", "urban_type"
        ]]

        # Household municipality
        df_households["commune_id"] = df_households["RESCOMM"].astype(str)
        df_persons = pd.merge(df_persons, df_households[["household_id", "commune_id"]], how = "left")
        assert np.all(~df_persons["commune_id"].isna())
        
        # Impute urban type
        df_persons = pd.merge(df_persons, df_urban_type, on = "commune_id", how = "left")
        df_persons["urban_type"] = df_persons["urban_type"].fillna("none").astype("category")

        df_households.drop(columns = ["commune_id"])
        df_persons.drop(columns = ["commune_id"])

    # Trip purpose
    df_trips["following_purpose"] = "other"
    df_trips["preceding_purpose"] = "other"

    for category, purpose in PURPOSE_MAP.items():
        df_trips.loc[df_trips["DESTMOT_H9"] == category, "following_purpose"] = purpose
        df_trips.loc[df_trips["ORMOT_H9"] == category, "preceding_purpose"] = purpose

    df_trips["following_purpose"] = df_trips["following_purpose"].astype("category")
    df_trips["preceding_purpose"] = df_trips["preceding_purpose"].astype("category")

    # Trip mode
    df_trips["mode"] = "pt"

    for category, mode in MODES_MAP.items():
        df_trips.loc[df_trips["MODP_H7"] == category, "mode"] = mode

    df_trips["mode"] = df_trips["mode"].astype("category")

    # Further trip attributes
    df_trips["euclidean_distance"] = df_trips["DPORTEE"] * 1000.0

    # Trip times
    df_trips["departure_time"] = df_trips["ORH"] * 3600.0 + df_trips["ORM"] * 60.0
    df_trips["arrival_time"] = df_trips["DESTH"] * 3600.0 + df_trips["DESTM"] * 60.0
    df_trips = hts.fix_trip_times(df_trips)

    # Durations
    df_trips["trip_duration"] = df_trips["arrival_time"] - df_trips["departure_time"]
    hts.compute_activity_duration(df_trips)

    # Add weight to trips
    df_trips = pd.merge(
        df_trips, df_persons[["person_id", "person_weight"]], on = "person_id", how = "left"
    ).rename(columns = { "person_weight": "trip_weight" })
    df_persons["trip_weight"] = df_persons["person_weight"]

    # Chain length
    df_persons["number_of_trips"] = df_persons["NBDEPL"].fillna(0).astype(int)

    # Passenger attribute
    df_persons["is_passenger"] = df_persons["person_id"].isin(
        df_trips[df_trips["mode"] == "car_passenger"]["person_id"].unique()
    )

    # Calculate consumption units
    hts.check_household_size(df_households, df_persons)
    df_households = pd.merge(df_households, hts.calculate_consumption_units(df_persons), on = "household_id")

    # Socioprofessional class
    df_persons["socioprofessional_class"] = df_persons["CS8"].fillna(8).astype(int)

    # Drop people that have NaN departure or arrival times in trips
    # Filter for people with NaN departure or arrival times in trips
    f = df_trips["departure_time"].isna()
    f |= df_trips["arrival_time"].isna()

    f = df_persons["person_id"].isin(df_trips[f]["person_id"])

    nan_count = np.count_nonzero(f)
    total_count = len(df_persons)

    print("Dropping %d/%d persons because of NaN values in departure and arrival times" % (nan_count, total_count))

    df_persons = df_persons[~f]
    df_trips = df_trips[df_trips["person_id"].isin(df_persons["person_id"].unique())]
    df_households = df_households[df_households["household_id"].isin(df_persons["household_id"])]

    # Fix activity types (because of inconsistent EGT data and removing in the timing fixing step)
    hts.fix_activity_types(df_trips)

    return df_households, df_persons, df_trips

def calculate_income_class(df):
    assert "household_income" in df
    assert "consumption_units" in df

    return np.digitize(df["household_income"] / df["consumption_units"], INCOME_CLASS_BOUNDS, right = True)
