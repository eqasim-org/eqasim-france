import pandas as pd
import numpy as np
import data.hts.hts as hts

"""
This stage cleans the Gironde EMC2.
"""

def configure(context):
    context.stage("data.hts.emc2_33.raw")
    if context.config("use_urban_type",False):
        context.stage("data.hts.emc2_33.urban_type")
    
    context.config("departments", [])
    
PURPOSE_MAP = {
    "home": [1, 2],
    "work": [11, 12, 13, 81],
    "education": [21, 22, 23, 24, 25, 26, 27, 28, 29],
    "shop": [30, 31, 32, 33, 34, 35, 82],
    "leisure": [51, 52, 53, 54],
    "other": [41, 42, 43, 61, 62, 63, 64, 71, 72, 73, 74, 91]
}

MODES_MAP = {
    "car": [13, 15, 21, 81],
    "car_passenger": [14, 16, 22, 82],
    "pt": [31, 32, 34, 36, 37, 39, 39, 41, 42, 51, 52, 53, 61, 62, 71],
    "bike": [11, 12, 17, 18, 93, 96, 97],
    "walk": [1]
}


def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.emc2_33.raw")
    requested_department = context.config("departments")[0]

    # set ids for households, persons, trips
    df_households["departement_id"] = requested_department
    df_households["edgt_household_id"] = df_households["MP2"].astype("int64")*100000000 + df_households["ECH"].astype(int)*1000

    df_persons["edgt_household_id"] =  df_persons["PP2"].astype("int64")*100000000 + df_persons["ECH"].astype(int)*1000
    df_persons["edgt_person_id"] = df_persons["PP2"].astype("int64")*100000000 + df_persons["ECH"].astype(int)*1000 + df_persons["PER"].astype(int)*100

    df_trips["edgt_household_id"] = df_trips["DP2"].astype("int64")*100000000 + df_trips["ECH"].astype(int)*1000
    df_trips["edgt_person_id"] =  df_trips["DP2"].astype("int64")*100000000 + df_trips["ECH"].astype(int)*1000 + df_trips["PER"].astype(int)*100
    df_trips["edgt_trip_id"] = df_trips["DP2"].astype("int64")*100000000 + df_trips["ECH"].astype(int)*1000 + df_trips["PER"].astype(int)*100 + df_trips["NDEP"].astype(int)

    # Construct new IDs for households, persons and trips (which are unique globally)
    df_households["household_id"] = np.arange(len(df_households))

    df_persons = pd.merge(
        df_persons, df_households[["edgt_household_id", "household_id", "departement_id"]],
        on = ["edgt_household_id"]
    ).sort_values(by = ["household_id", "edgt_person_id"])
    df_persons["person_id"] = np.arange(len(df_persons))

    df_trips = pd.merge(
        df_trips, df_persons[["edgt_person_id", "edgt_household_id", "person_id", "household_id"]],
        on = ["edgt_person_id", "edgt_household_id"]
    ).sort_values(by = ["household_id", "person_id", "edgt_trip_id"])
    df_trips["trip_id"] = np.arange(len(df_trips))

    # Trip flags
    df_trips = hts.compute_first_last(df_trips)

    # Weight
    df_persons["person_weight"] = df_persons["COEP"].astype(float)
    df_households["household_weight"] = df_households["COEM"].astype(float)

    # Clean age
    df_persons["age"] = df_persons["P4"].astype(int)

    # Clean sex
    df_persons.loc[df_persons["P2"] == 1, "sex"] = "male"
    df_persons.loc[df_persons["P2"] == 2, "sex"] = "female"
    df_persons["sex"] = df_persons["sex"].astype("category")

    # Household size
    df_size = df_persons.groupby("household_id").size().reset_index(name = "household_size")
    df_households = pd.merge(df_households, df_size, on = "household_id")

    # Clean departement
    df_trips.loc[df_trips["D3"] <900000000,"origin_departement_id"] = requested_department #
    df_trips.loc[df_trips["D3"] >=900000000,"origin_departement_id"] = "99" #

    df_trips.loc[df_trips["D7"] <900000000,"destination_departement_id"] = requested_department #
    df_trips.loc[df_trips["D7"] >900000000,"destination_departement_id"] = "99" #

    df_households["departement_id"] = df_households["departement_id"].astype("category")
    df_persons["departement_id"] = df_persons["departement_id"].astype("category")
    df_trips["origin_departement_id"] = df_trips["origin_departement_id"].astype("category")
    df_trips["destination_departement_id"] = df_trips["destination_departement_id"].astype("category")

    # Household set zone ID
    df_households["zone_id"] = df_households["MP2"]

    # Clean employment
    df_persons["employed"] = df_persons["P7"].isin(["1", "2"])

    # Studies
    df_persons["studies"] = df_persons["P7"].isin(["3", "4", "5"])

    # Number of vehicles
    df_households["number_of_vehicles"] = df_households["M14"] + df_households["M5"]
    df_households["number_of_vehicles"] = df_households["number_of_vehicles"].astype(int)
    df_households["number_of_bikes"] = df_households["M20"].astype(int)

    # License
    df_persons["has_license"] = df_persons["P5"] == "1"

    # Has subscription (not availabile in EDGT 44)
    df_persons["has_pt_subscription"] = df_persons["P10"] == "1"

    # Survey respondents
    # PENQ 1 : fully awnsered the travel questionary section, having a chain or non-movers
    # PENQ 2 : nonrespondent of travel questionary section
    df_persons.loc[df_persons["PENQ"] == 1, "travel_respondent"] = True
    df_persons.loc[df_persons["PENQ"] == 2, "travel_respondent"] = False

    assert np.count_nonzero(df_persons["travel_respondent"].isna()) == 0

    # Trip purpose
    df_trips["following_purpose"] = "invalid"
    df_trips["preceding_purpose"] = "invalid"

    for purpose, values in PURPOSE_MAP.items():
        df_trips.loc[df_trips["D5A"].isin(values), "following_purpose"] = purpose
        df_trips.loc[df_trips["D2A"].isin(values), "preceding_purpose"] = purpose

    assert np.count_nonzero(df_trips["following_purpose"] == "invalid") == 0
    assert np.count_nonzero(df_trips["preceding_purpose"] == "invalid") == 0

    df_trips["following_purpose"] = df_trips["following_purpose"].astype("category")
    df_trips["preceding_purpose"] = df_trips["preceding_purpose"].astype("category")

    # Trip mode
    df_trips["mode"] = "invalid"

    for mode, values in MODES_MAP.items():
        df_trips.loc[df_trips["MODP"].isin(values), "mode"] = mode

    df_trips.loc[df_trips["mode"] == "invalid","mode"] = "car"

    assert np.count_nonzero(df_trips["mode"] == "invalid") == 0
    df_trips["mode"] = df_trips["mode"].astype("category")

    # Further trip attributes
    df_trips["euclidean_distance"] = df_trips["DOIB"]
    df_trips["routed_distance"] = df_trips["DIST"]

    # Trip times
    df_trips["departure_time"] = 3600.0 * df_trips["D4"].str[:2].astype(int) # hour
    df_trips["departure_time"] += 60.0 * df_trips["D4"].str[2:].astype(int) # minute

    df_trips["arrival_time"] = 3600.0 * df_trips["D8"].str[:2].astype(int) # hour
    df_trips["arrival_time"] += 60.0 * df_trips["D8"].str[2:].astype(int) # minute

    df_trips = df_trips.sort_values(by = ["household_id", "person_id", "trip_id"])
    df_trips = hts.fix_trip_times(df_trips)

    # Durations
    df_trips["trip_duration"] = df_trips["arrival_time"] - df_trips["departure_time"]
    hts.compute_activity_duration(df_trips)

    # Add weight to trips
    df_trips = pd.merge(
        df_trips, df_persons[["person_id", "COEQ"]], on = "person_id", how = "left"
    ).rename(columns = { "COEQ": "trip_weight" })
    df_persons["trip_weight"] = df_persons["COEQ"]

    # Chain length
    df_count = df_trips[["person_id"]].groupby("person_id").size().reset_index(name = "number_of_trips")
    # People with at least one trip (number_of_trips > 0)
    df_persons = pd.merge(df_persons, df_count, on = "person_id", how = "left")
    # People that awnsered the travel questionary section but stayed at home (number_of_trips = 0)
    df_persons.loc[(df_persons["travel_respondent"] == True) & (df_persons["number_of_trips"].isna()), "number_of_trips"]  = 0
    # Nonrespondent of travel questionary section (number_of_trips = -1)
    df_persons["number_of_trips"] = df_persons["number_of_trips"].fillna(-1).astype(int)

    # Passenger attribute
    df_persons["is_passenger"] = df_persons["person_id"].isin(
        df_trips[df_trips["mode"] == "car_passenger"]["person_id"].unique()
    )

    # Calculate consumption units
    hts.check_household_size(df_households, df_persons)
    df_households = pd.merge(df_households, hts.calculate_consumption_units(df_persons), on = "household_id")

    # # Socioprofessional class
    df_persons["socioprofessional_class"] = df_persons["P9"].fillna(8).astype(int)
    df_persons.loc[df_persons["socioprofessional_class"] > 6, "socioprofessional_class"] = 8
    df_persons.loc[df_persons["P7"] == "7", "socioprofessional_class"] = 7

    # Check departure and arrival times
    assert np.count_nonzero(df_trips["departure_time"].isna()) == 0
    assert np.count_nonzero(df_trips["arrival_time"].isna()) == 0

    # Fix activity types (because of inconsistent EGT data and removing in the timing fixing step)
    hts.fix_activity_types(df_trips)
    
    if context.config("use_urban_type"):
        df_urban_type = context.stage("data.hts.emc2_33.urban_type")
        number_of_households = len(df_households)
        df_households = df_households.merge(df_urban_type[["zone_id","urban_type"]],on="zone_id",how="left")
        assert len(df_households) == number_of_households

    return df_households, df_persons, df_trips
