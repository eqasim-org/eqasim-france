from tqdm import tqdm
import pandas as pd
import numpy as np
import data.hts.hts as hts

"""
This stage cleans the national HTS.
"""

def configure(context):
    context.stage("data.hts.entd.raw")

INCOME_CLASS_BOUNDS = [400, 600, 800, 1000, 1200, 1500, 1800, 2000, 2500, 3000, 4000, 6000, 10000, 1e6]

PURPOSE_MAP = [
    ("1", "home"),
    ("1.11", "education"),
    ("2", "shop"),
    ("3", "other"),
    ("4", "other"),
    ("5", "leisure"),
    ("6", "other"),
    ("7", "leisure"),
    ("8", "leisure"),
    ("9", "work")
]

MODES_MAP = [
    ("1", "walk"),
    ("2", "car"), #
    ("2.20", "bicycle"), # bike
    ("2.23", "car_passenger"), # motorcycle passenger
    ("2.25", "car_passenger"), # same
    ("3", "car"),
    ("3.32", "car_passenger"),
    ("4", "pt"), # taxi
    ("5", "pt"),
    ("6", "pt"),
    ("7", "pt"), # Plane
    ("8", "pt"), # Boat
#    ("9", "pt") # Other
]

def convert_time(x):
    return np.dot(np.array(x.split(":"), dtype = float), [3600.0, 60.0, 1.0])

def execute(context):
    df_individu, df_tcm_individu, df_menage, df_tcm_menage, df_deploc = context.stage("data.hts.entd.raw")

    # Make copies
    df_persons = pd.DataFrame(df_tcm_individu, copy = True)
    df_households = pd.DataFrame(df_tcm_menage, copy = True)
    df_trips = pd.DataFrame(df_deploc, copy = True)

    # Get weights for persons that actually have trips
    df_persons = pd.merge(df_persons, df_trips[["IDENT_IND", "PONDKI"]].drop_duplicates("IDENT_IND"), on = "IDENT_IND", how = "left")
    df_persons["is_kish"] = ~df_persons["PONDKI"].isna()
    df_persons["trip_weight"] = df_persons["PONDKI"].fillna(0.0)

    # Important: If someone did not have any trips on the reference day, ENTD asked
    # for another day. With this flag we make sure that we only cover "reference days".
    f = df_trips["V2_MOBILREF"] == 1
    df_trips = df_trips[f]
    print("Filtering out %d non-reference day trips" % np.count_nonzero(~f))

    # Merge in additional information from ENTD
    df_households = pd.merge(df_households, df_menage[[
        "idENT_MEN", "V1_JNBVEH", "V1_JNBMOTO", "V1_JNBCYCLO", "V1_JNBVELOADT"
    ]], on = "idENT_MEN", how = "left")

    df_persons = pd.merge(df_persons, df_individu[[
        "IDENT_IND", "V1_GPERMIS", "V1_GPERMIS2R", "V1_ICARTABON"
    ]], on = "IDENT_IND", how = "left")

    # Transform original IDs to integer (they are hierarchichal)
    df_persons["entd_person_id"] = df_persons["IDENT_IND"].astype(int)
    df_persons["entd_household_id"] = df_persons["IDENT_MEN"].astype(int)
    df_households["entd_household_id"] = df_households["idENT_MEN"].astype(int)
    df_trips["entd_person_id"] = df_trips["IDENT_IND"].astype(int)

    # Construct new IDs for households, persons and trips (which are unique globally)
    df_households["household_id"] = np.arange(len(df_households))

    df_persons = pd.merge(
        df_persons, df_households[["entd_household_id", "household_id"]],
        on = "entd_household_id"
    )
    df_persons["person_id"] = np.arange(len(df_persons))

    df_trips = pd.merge(
        df_trips, df_persons[["entd_person_id", "person_id", "household_id"]],
        on = ["entd_person_id"]
    )
    df_trips["trip_id"] = np.arange(len(df_trips))

    # Weight
    df_persons["person_weight"] = df_persons["PONDV1"].astype(float)
    df_households["household_weight"] = df_households["PONDV1"].astype(float)

    # Clean age
    df_persons.loc[:, "age"] = df_persons["AGE"]

    # Clean sex
    df_persons.loc[df_persons["SEXE"] == 1, "sex"] = "male"
    df_persons.loc[df_persons["SEXE"] == 2, "sex"] = "female"
    df_persons["sex"] = df_persons["sex"].astype("category")

    # Household size
    df_households["household_size"] = df_households["NPERS"]

    # Clean departement
    df_households["departement_id"] = df_households["DEP"].fillna("undefined").astype("category")
    df_persons["departement_id"] = df_persons["DEP"].fillna("undefined").astype("category")

    df_trips["origin_departement_id"] = df_trips["V2_MORIDEP"].fillna("undefined").astype("category")
    df_trips["destination_departement_id"] = df_trips["V2_MDESDEP"].fillna("undefined").astype("category")

    # Clean urban type
    df_households["urban_type"] = df_households["numcom_UU2010"].replace({
        "B": "suburb",
        "C": "central_city",
        "I": "isolated_city",
        "R": "none"
    })

    assert np.all(~df_households["urban_type"].isna())
    df_households["urban_type"] = df_households["urban_type"].astype("category")

    # Clean employment
    df_persons["employed"] = df_persons["SITUA"].isin([1, 2])

    # Studies
    # Many < 14 year old have NaN
    df_persons["studies"] = df_persons["ETUDES"].fillna(1) == 1
    df_persons.loc[df_persons["age"] < 5, "studies"] = False

    # Number of vehicles
    df_households["number_of_cars"] = df_households["V1_JNBVEH"].fillna(0)
    df_households["number_of_cars"] += df_households["V1_JNBMOTO"].fillna(0) # motorbike
    df_households["number_of_cars"] += df_households["V1_JNBCYCLO"].fillna(0) # motorbike
    df_households["number_of_cars"] = df_households["number_of_cars"].astype(int)

    df_households["number_of_bicycles"] = df_households["V1_JNBVELOADT"].fillna(0).astype(int)

    # License
    df_persons["has_license"] = (df_persons["V1_GPERMIS"] == 1) | (df_persons["V1_GPERMIS2R"] == 1)

    # Has subscription
    df_persons["has_pt_subscription"] = df_persons["V1_ICARTABON"] == 1

    # Household income
    df_households["income_class"] = -1
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("Moins de 400"), "income_class"] = 0
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 400"), "income_class"] = 1
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 600"), "income_class"] = 2
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 800"), "income_class"] = 3
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 1 000"), "income_class"] = 4
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 1 200"), "income_class"] = 5
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 1 500"), "income_class"] = 6
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 1 800"), "income_class"] = 7
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 2 000"), "income_class"] = 8
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 2 500"), "income_class"] = 9
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 3 000"), "income_class"] = 10
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 4 000"), "income_class"] = 11
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("De 6 000"), "income_class"] = 12
    df_households.loc[df_households["TrancheRevenuMensuel"].str.startswith("10 000"), "income_class"] = 13
    df_households["income_class"] = df_households["income_class"].astype(int)

    # Trip purpose
    df_trips["following_purpose"] = "other"
    df_trips["preceding_purpose"] = "other"

    for prefix, activity_type in PURPOSE_MAP:
        df_trips.loc[
            df_trips["V2_MMOTIFDES"].astype(str).str.startswith(prefix), "following_purpose"
        ] = activity_type

        df_trips.loc[
            df_trips["V2_MMOTIFORI"].astype(str).str.startswith(prefix), "preceding_purpose"
        ] = activity_type

    df_trips["following_purpose"] = df_trips["following_purpose"].astype("category")
    df_trips["preceding_purpose"] = df_trips["preceding_purpose"].astype("category")

    # Trip mode
    df_trips["mode"] = "pt"

    for prefix, mode in MODES_MAP:
        df_trips.loc[
            df_trips["V2_MTP"].astype(str).str.startswith(prefix), "mode"
        ] = mode

    df_trips["mode"] = df_trips["mode"].astype("category")

    # Further trip attributes
    df_trips["routed_distance"] = df_trips["V2_MDISTTOT"] * 1000.0
    df_trips["routed_distance"] = df_trips["routed_distance"].fillna(0.0) # This should be just one within Île-de-France

    # Only leave weekday trips
    f = df_trips["V2_TYPJOUR"] == 1
    print("Removing %d trips on weekends" % np.count_nonzero(~f))
    df_trips = df_trips[f]

    # Only leave one day per person
    initial_count = len(df_trips)

    df_first_day = df_trips[["person_id", "IDENT_JOUR"]].sort_values(
        by = ["person_id", "IDENT_JOUR"]
    ).drop_duplicates("person_id")
    df_trips = pd.merge(df_trips, df_first_day, how = "inner", on = ["person_id", "IDENT_JOUR"])

    final_count = len(df_trips)
    print("Removed %d trips for non-primary days" % (initial_count - final_count))

    # Trip flags
    df_trips = hts.compute_first_last(df_trips)

    # Trip times
    df_trips["departure_time"] = df_trips["V2_MORIHDEP"].apply(convert_time).astype(float)
    df_trips["arrival_time"] = df_trips["V2_MDESHARR"].apply(convert_time).astype(float)
    df_trips = hts.fix_trip_times(df_trips)

    # Durations
    df_trips["trip_duration"] = df_trips["arrival_time"] - df_trips["departure_time"]
    hts.compute_activity_duration(df_trips)

    # Add weight to trips
    df_trips["trip_weight"] = df_trips["PONDKI"]

    # Chain length
    df_persons = pd.merge(
        df_persons, df_trips[["person_id", "NDEP"]].drop_duplicates("person_id").rename(columns = { "NDEP": "number_of_trips" }),
        on = "person_id", how = "left"
    )
    df_persons["number_of_trips"] = df_persons["number_of_trips"].fillna(-1).astype(int)
    df_persons.loc[(df_persons["number_of_trips"] == -1) & df_persons["is_kish"], "number_of_trips"] = 0

    # Calculate consumption units
    hts.check_household_size(df_households, df_persons)
    df_households = pd.merge(df_households, hts.calculate_consumption_units(df_persons), on = "household_id")

    # Socioprofessional class
    df_persons["socioprofessional_class"] = df_persons["CS24"].fillna(80).astype(int) // 10

    # Fix activity types (because of 1 inconsistent ENTD data)
    hts.fix_activity_types(df_trips)

    return df_households, df_persons, df_trips

def calculate_income_class(df):
    assert "household_income" in df
    assert "consumption_units" in df

    return np.digitize(df["household_income"], INCOME_CLASS_BOUNDS, right = True)
