import pandas as pd
import numpy as np
import data.hts.hts as hts

"""
This stage cleans the the French HTS (EMP).
"""

def configure(context):
    context.stage("data.hts.emp.raw")

INCOME_CLASS_BOUNDS = [400, 800, 1000, 1200, 1500, 1800, 2000, 2500, 4000, 10000, 1e6]

PURPOSE_MAP = [
    ("1", "home"),
    ("1.4", "education"),
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
    ("2.1", "bike"), # bike
    ("2.2", "bike"), # bike-sharing 
    ("2.4", "car_passenger"), # motorcycle passenger
    ("2.6", "car_passenger"), # same
    ("3", "car"),
    ("3.2", "car_passenger"),
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
    df_individu, df_tcm_individu,df_tcm_individu_kish, df_menage, df_tcm_menage, df_deploc = context.stage("data.hts.emp.raw")

    # Make copies
    df_persons = pd.DataFrame(df_tcm_individu, copy = True).rename(columns={"ident_ind":"IDENT_IND", "ident_men":"IDENT_MEN"})
    df_households = pd.DataFrame(df_tcm_menage, copy = True).rename(columns={ "ident_men":"IDENT_MEN"})
    df_trips = pd.DataFrame(df_deploc, copy = True)
    
    # Get weights for persons that actually have trips
    df_persons = pd.merge(df_persons, df_trips[["IDENT_IND", "POND_JOUR"]].drop_duplicates("IDENT_IND"), on = "IDENT_IND", how = "left")
    df_persons["is_kish"] = ~df_persons["POND_JOUR"].isna()
    df_persons["trip_weight"] = df_persons["POND_JOUR"].fillna(0.0)

    # Merge in additional information from EMP
    df_households = pd.merge(df_households, df_menage[[
        "IDENT_MEN", "JNBVELOAD",
    "JNBVEH", "JNBMOTO", "JNBCYCLO"
    ]], on = "IDENT_MEN", how = "left")

    df_persons = pd.merge(df_persons, df_tcm_individu_kish[["AGE", "ident_ind","CS24", "SITUA",
    ]].rename(columns={"ident_ind":"IDENT_IND"}), on = "IDENT_IND", how = "left")

    df_persons = pd.merge(df_persons, df_individu[[
        "IDENT_IND", "BPERMIS", "BCARTABON","ETUDIE","pond_indC"
    ]], on = "IDENT_IND", how = "left")
    
    # Transform original IDs to integer (they are hierarchichal)
    df_persons["emp_person_id"] = df_persons["IDENT_IND"].astype(int)
    df_persons["emp_household_id"] = df_persons["IDENT_MEN"].astype(int)
    df_households["emp_household_id"] = df_households["IDENT_MEN"].astype(int)
    df_trips["emp_person_id"] = df_trips["IDENT_IND"].astype(int)

    # Construct new IDs for households, persons and trips (which are unique globally)
    df_households["household_id"] = np.arange(len(df_households))

    df_persons = pd.merge(
        df_persons, df_households[["emp_household_id", "household_id","DEP_RES"]],
        on = "emp_household_id"
    )
    df_persons["person_id"] = np.arange(len(df_persons))
    
    df_trips = pd.merge(
        df_trips, df_persons[["emp_person_id", "person_id", "household_id"]],
        on = ["emp_person_id"]
    )
    df_trips["trip_id"] = np.arange(len(df_trips))

    # Weight
    df_persons["person_weight"] = df_persons["pond_indC"].astype(float)
    df_households["household_weight"] = df_households["pond_menC"].astype(float)

    # Clean age
    df_persons.loc[:, "age"] = df_persons["AGE"].fillna(0)

    # Clean sex
    df_persons.loc[df_persons["SEXE"] == 1, "sex"] = "male"
    df_persons.loc[df_persons["SEXE"] == 2, "sex"] = "female"
    df_persons["sex"] = df_persons["sex"].astype("category")

    # Household size
    df_households["household_size"] = df_households["NPERS"]

    # Clean departement
    df_households["departement_id"] = df_households["DEP_RES"].fillna("undefined").astype("category")
    df_persons["departement_id"] = df_persons["DEP_RES"].fillna("undefined").astype("category")

    df_trips["origin_departement_id"] = '00'
    df_trips["destination_departement_id"] = '00'

    # Clean urban type
    df_households["urban_type"] = df_households["STATUTCOM_UU_RES"].replace({
        "B": "suburb",
        "C": "central_city",
        "I": "isolated_city",
        "H": "none"
    })

    assert np.all(~df_households["urban_type"].isna())
    df_households["urban_type"] = df_households["urban_type"].astype("category")

    # Clean employment
    df_persons["employed"] = df_persons["SITUA"].isin([1, 2])

    # Studies
    # Many < 14 year old have NaN
    df_persons["studies"] = df_persons["ETUDIE"].fillna(1) == 1
    df_persons.loc[df_persons["age"] < 5, "studies"] = False

    # Number of vehicles
    df_households["number_of_vehicles"] = 0
    df_households["number_of_vehicles"] += df_households["JNBVEH"].fillna(0)
    df_households["number_of_vehicles"] += df_households["JNBMOTO"].fillna(0)
    df_households["number_of_vehicles"] += df_households["JNBCYCLO"].fillna(0)
    df_households["number_of_vehicles"] = df_households["number_of_vehicles"].astype(int)

    df_households["number_of_bikes"] = df_households["JNBVELOAD"].fillna(0).astype(int)

    # License
    df_persons["has_license"] = df_persons["BPERMIS"] == 1

    # Has subscription
    df_persons["has_pt_subscription"] = df_persons["BCARTABON"] == 1

    # Household income
    df_households["income_class"] = df_households["decile_rev"] -1
    df_households["income_class"] = df_households["income_class"].astype(int)

    # Trip purpose
    df_trips["following_purpose"] = "other"
    df_trips["preceding_purpose"] = "other"

    for prefix, activity_type in PURPOSE_MAP:
        df_trips.loc[
            df_trips["MMOTIFDES"].astype(str).str.startswith(prefix), "following_purpose"
        ] = activity_type

        df_trips.loc[
            df_trips["MOTPREC"].astype(str).str.startswith(prefix), "preceding_purpose"
        ] = activity_type

    df_trips["following_purpose"] = df_trips["following_purpose"].astype("category")
    df_trips["preceding_purpose"] = df_trips["preceding_purpose"].astype("category")

    # Trip mode
    df_trips["mode"] = "pt"

    for prefix, mode in MODES_MAP:
        df_trips.loc[
            df_trips["mtp"].astype(str).str.startswith(prefix), "mode"
        ] = mode

    df_trips["mode"] = df_trips["mode"].astype("category")

    # Further trip attributes
    df_trips["routed_distance"] = df_trips["MDISTTOT_fin"] * 1000.0
    df_trips["routed_distance"] = df_trips["routed_distance"].fillna(0.0) # This should be just one within Île-de-France

    # Only leave weekday trips
    f = df_trips["TYPEJOUR"] == 1
    print("Removing %d trips on weekends" % np.count_nonzero(~f))
    df_trips = df_trips[f]

    # Only leave one day per person
    initial_count = len(df_trips)

    df_first_day = df_trips[["person_id","MDATE_jour","MDATE_mois"]].sort_values(
        by = ["person_id", "MDATE_jour","MDATE_mois"]
    ).drop_duplicates("person_id")
    df_trips = pd.merge(df_trips, df_first_day, how = "inner", on = ["person_id", "MDATE_jour","MDATE_mois"])

    final_count = len(df_trips)
    print("Removed %d trips for non-primary days" % (initial_count - final_count))

    # Trip flags
    df_trips = hts.compute_first_last(df_trips)

    # Trip times
    df_trips["departure_time"] = df_trips["MORIHDEP"].apply(convert_time).astype(float)
    df_trips["arrival_time"] = df_trips["MDESHARR"].apply(convert_time).astype(float)
    df_trips = hts.fix_trip_times(df_trips)

    # Durations
    df_trips["trip_duration"] = df_trips["arrival_time"] - df_trips["departure_time"]
    hts.compute_activity_duration(df_trips)

    # Add weight to trips
    df_trips["trip_weight"] = df_trips["POND_JOUR"]

    # Chain length
    df_persons = pd.merge(
        df_persons, df_trips[["person_id", "nb_dep"]].drop_duplicates("person_id").rename(columns = { "nb_dep": "number_of_trips" }),
        on = "person_id", how = "left"
    )
    df_persons["number_of_trips"] = df_persons["number_of_trips"].fillna(-1).astype(int)
    df_persons.loc[(df_persons["number_of_trips"] == -1) & df_persons["is_kish"], "number_of_trips"] = 0

    # Passenger attribute
    df_persons["is_passenger"] = df_persons["person_id"].isin(
        df_trips[df_trips["mode"] == "car_passenger"]["person_id"].unique()
    )
    
    #Drop person without right household size 
    df_persons = df_persons.drop(df_persons[(df_persons["number_of_trips"] == -1) & (df_persons['household_id'].isin([1647,6182,12630]))].index)
    
    # Calculate consumption units
    hts.check_household_size(df_households, df_persons)
    df_households = pd.merge(df_households, hts.calculate_consumption_units(df_persons), on = "household_id")

    # Socioprofessional class
    df_persons["socioprofessional_class"] = df_persons["CS24"].fillna(80).astype(int) // 10

    # Fix activity types (because of 1 inconsistent emp data)
    hts.fix_activity_types(df_trips)

    return df_households, df_persons, df_trips

def calculate_income_class(df):
    assert "household_income" in df
    assert "consumption_units" in df

    return np.digitize(df["household_income"], INCOME_CLASS_BOUNDS, right = True)
