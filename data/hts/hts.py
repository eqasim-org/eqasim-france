import pandas as pd
import numpy as np

def swap_departure_arrival_times(df, f):
    assert "arrival_time" in df
    assert "departure_time" in df

    departure_times = df[f]["departure_time"].values
    arrival_times = df[f]["arrival_time"].values

    df.loc[f, "departure_time"] = arrival_times
    df.loc[f, "arrival_time"] = departure_times

def fix_trip_times(df_trips):
    """
    - Negative duration:
        - Departure and arrival time may be switched
        - Trip goes over midnight

    - Current trip is after following trip:
        - Following trip may be on the next day

    - Intresecting trips
    """
    columns = ["trip_id", "person_id", "departure_time", "arrival_time", "preceding_purpose", "following_purpose", "is_first_trip", "is_last_trip"]
    df_main = df_trips
    df_next = df_main.shift(-1)
    df_previous = df_main.shift(1)

    # 1) Negative trip durations
    f_negative = df_main["departure_time"] > df_main["arrival_time"]
    print("Found %d occurences with negative duration" % np.count_nonzero(f_negative))

    # 1.1) Departure and arrival time may have been swapped, and chain is consistent
    f_swap = np.asarray(f_negative).copy()
    f_swap &= (df_main["arrival_time"] > df_previous["arrival_time"]) | df_main["is_first_trip"]
    f_swap &= (df_main["departure_time"] < df_next["departure_time"]) | df_main["is_last_trip"]
    print("  of which %d can swap departure and arrival time without conflicts with previous or following trip" % np.count_nonzero(f_swap))

    swap_departure_arrival_times(df_main, f_swap)
    f_negative[f_swap] = False

    # 1.2) Departure and arrival time may have been swapped, but chain is not consistent
    #      However, the offset duration is unlikely to be a trip over midnight
    offset = df_main["departure_time"] - df_main["arrival_time"]
    f_swap = (offset > 0) & (offset < 10 * 3600)
    print("  of which %d are unlikely to cover midnight, so we swap arrival and departure time although there are conflicts" % np.count_nonzero(f_swap))

    swap_departure_arrival_times(df_main, f_swap)
    f_negative[f_swap] = False

    # 1.3) Covering midnight -> Shift arrival time
    print("  of which %d seem to cover midnight, so we shift arrival time by 24h" % np.count_nonzero(f_negative))
    df_main.loc[f_negative, "arrival_time"] += 24 * 3600.0

    # 2) Current trip is after following trip
    #    = preceding trip is after current trip
    shifted_count = 1
    round = 0

    print("Shifting trips that should start after midnight")
    while shifted_count > 0:
        df_previous = df_main.shift(1)

        f_shift = ~df_main["is_first_trip"]
        f_shift &= df_previous["departure_time"] > df_main["arrival_time"]
        f_shift &= df_previous["arrival_time"] > df_main["arrival_time"]

        df_main.loc[f_shift, "departure_time"] += 24 * 3600.0
        df_main.loc[f_shift, "arrival_time"] += 24 * 3600.0

        shifted_count = np.count_nonzero(f_shift)
        round += 1

        if shifted_count > 0:
            print("  Shifted %d trips in round %d" % (shifted_count, round))
        else:
            print("  No more occurences where current trip is after the next")

    df_next = df_main.shift(-1)
    df_previous = df_main.shift(1)

    # Intersecting trips
    f = ~df_main["is_last_trip"]
    f &= df_main["arrival_time"] > df_next["departure_time"]
    print("Found %d occurences where current trip ends after next trip starts" % np.count_nonzero(f))

    f &= df_main["departure_time"] <= df_next["departure_time"]
    print("  of which we're able to shorten %d to make it consistent" % np.count_nonzero(f))
    df_main.loc[f, "arrival_time"] = df_next["departure_time"]

    # Included trips (moving the first one to the start of the following trip and setting duration to zero)
    f = ~df_main["is_last_trip"]
    f &= df_main["departure_time"] >= df_next["departure_time"]
    f &= df_main["arrival_time"] <= df_next["arrival_time"]
    df_main.loc[f, "departure_time"] = df_next["departure_time"]
    df_main.loc[f, "arrival_time"] = df_next["departure_time"]
    print("Found %d occurences where current trip is included in next trip" % np.count_nonzero(f))

    return df_main

def check_trip_times(df_trips):
    print("Validating trip times...")
    any_errors = False
    df_next = df_trips.shift(-1)

    f = df_trips["departure_time"] < 0.0
    print("  Trips with negative departure time:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = df_trips["arrival_time"] < 0.0
    print("  Trips with negative arrival time:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = df_trips["departure_time"] > df_trips["arrival_time"]
    print("  Trips with negative duration:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = ~df_trips["is_last_trip"]
    f &= df_trips["arrival_time"] > df_next["departure_time"]
    print("  Trips that arrive after next departure:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = ~df_trips["is_last_trip"]
    f &= df_trips["departure_time"] < df_next["departure_time"]
    f &= df_trips["arrival_time"] > df_next["departure_time"]
    f &= df_trips["arrival_time"] < df_next["arrival_time"]
    print("  Trips that 'enter' following trip:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = ~df_trips["is_last_trip"]
    f &= df_trips["departure_time"] > df_next["departure_time"]
    f &= df_trips["arrival_time"] > df_next["arrival_time"]
    f &= df_trips["departure_time"] < df_next["arrival_time"]
    print("  Trips that 'exits' following trip", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = ~df_trips["is_last_trip"]
    f &= df_trips["departure_time"] > df_next["departure_time"]
    f &= df_trips["arrival_time"] > df_next["departure_time"]
    f &= df_trips["departure_time"] < df_next["arrival_time"]
    f &= df_trips["arrival_time"] < df_next["arrival_time"]
    print("  Trips that 'are included in' following trip:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = ~df_trips["is_last_trip"]
    f &= df_trips["departure_time"] < df_next["departure_time"]
    f &= df_trips["arrival_time"] > df_next["arrival_time"]
    print("  Trips that 'cover' following trip:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = ~df_trips["is_last_trip"]
    f &= df_trips["departure_time"] > df_next["arrival_time"]
    f &= df_trips["arrival_time"] > df_next["arrival_time"]
    print("  Trips that 'are after' following trip:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    f = df_trips["departure_time"].isna()
    f |= df_trips["arrival_time"].isna()
    f |= df_trips["trip_duration"].isna()
    print("  Trips that have NaN times:", np.count_nonzero(f))
    any_errors |= np.count_nonzero(f) > 0

    if any_errors:
        print("  !!! Errors while validating trip times")
        return False
    else:
        print("  => All trip times are consistent!")
        return True

def fix_activity_types(df_trips):
    f = (df_trips["preceding_purpose"] != df_trips["following_purpose"].shift(1)) & ~df_trips["is_first_trip"]
    df_trips.loc[f, "preceding_purpose"] = df_trips.shift(1)["following_purpose"][f].values
    print("Fixing %d inconsistent activity types" % np.count_nonzero(f))

    check_activity_types(df_trips)

def check_activity_types(df_trips):
    f  = (df_trips["following_purpose"] != df_trips["preceding_purpose"].shift(-1)) & ~df_trips["is_last_trip"]
    f |= (df_trips["following_purpose"].shift(1) != df_trips["preceding_purpose"]) & ~df_trips["is_first_trip"]

    error_count = np.count_nonzero(f)
    print("Trips with inconsistent activity types: %d" % error_count)

    return error_count == 0

def compute_first_last(df_trips):
    assert "person_id" in df_trips

    df_trips = df_trips.sort_values(by = ["person_id", "trip_id"])
    df_trips["is_first_trip"] = df_trips["person_id"].ne(df_trips["person_id"].shift(1))
    df_trips["is_last_trip"] = df_trips["person_id"].ne(df_trips["person_id"].shift(-1))

    return df_trips

def compute_activity_duration(df_trips):
    assert "departure_time" in df_trips
    assert "arrival_time" in df_trips

    df_next = df_trips.shift(-1)
    df_trips["activity_duration"] = df_next["departure_time"] - df_trips["arrival_time"]
    df_trips.loc[df_trips["is_last_trip"], "activity_duration"] = np.nan

def check_household_size(df_households, df_persons):
    df_size = df_persons.groupby("household_id").size().reset_index(name = "count")
    df_size = pd.merge(df_households[["household_id", "household_size"]], df_size, on = "household_id")

    assert len(df_size) == len(df_households)
    assert (df_size["household_size"] == df_size["count"]).all()

def calculate_consumption_units(df_persons):
    df_units = df_persons[["household_id", "age"]].copy()
    df_units["under_14"] = df_units["age"] < 14
    df_units["over_14"] = df_units["age"] >= 14
    df_units = df_units.groupby("household_id").sum().reset_index()

    df_units["consumption_units"] = 1.0
    df_units["consumption_units"] += df_units["under_14"] * 0.3
    df_units["consumption_units"] += np.maximum(0, df_units["over_14"] - 1) * 0.5

    return df_units[["household_id", "consumption_units"]]

HOUSEHOLD_COLUMNS = [
    "household_id", "household_weight", "household_size",
    "number_of_vehicles", "number_of_bikes", "departement_id",
    "consumption_units", # "income_class"
]

PERSON_COLUMNS = [
    "person_id", "household_id", "person_weight",
    "age", "sex", "employed", "studies",
    "has_license", "has_pt_subscription",
    "number_of_trips", "departement_id", "trip_weight",
    "is_passenger", "socioprofessional_class"
]

TRIP_COLUMNS = [
    "person_id", "trip_id", "trip_weight",
    "departure_time", "arrival_time",
    "trip_duration", "activity_duration",
    "following_purpose", "preceding_purpose", "is_last_trip", "is_first_trip",
    "mode", "origin_departement_id", "destination_departement_id"
]

def check(df_households, df_persons, df_trips):
    assert check_trip_times(df_trips)
    assert check_activity_types(df_trips)
    assert np.count_nonzero(df_trips["trip_duration"] < 0) == 0
    assert np.count_nonzero(df_trips["activity_duration"] < 0) == 0
    assert not (df_trips["activity_duration"].isna() & ~df_trips["is_last_trip"]).any()

    for column in HOUSEHOLD_COLUMNS:
        assert column in df_households

    for column in PERSON_COLUMNS:
        assert column in df_persons

    for column in TRIP_COLUMNS:
        assert column in df_trips

    if not ("routed_distance" in df_trips or "euclidean_distance" in df_trips):
        assert False

    if "routed_distance" in df_trips:
        assert not (df_trips["routed_distance"].isna()).any()

    if "euclidean_distance" in df_trips:
        assert not (df_trips["euclidean_distance"].isna()).any()
