import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as tck

"""
Comparison of various attributes between EGT, ENTD and census.
"""


def configure(context):
    context.stage("data.hts.egt.filtered")
    context.stage("data.hts.entd.filtered")
    context.stage("data.census.filtered")


def combine(htss):
    households, persons, trips = [], [], []

    for name, (df_hts_households, df_hts_persons, df_hts_trips) in htss.items():
        df_hts_households = pd.DataFrame(df_hts_households, copy=True)
        df_hts_persons = pd.DataFrame(df_hts_persons, copy=True)
        df_hts_trips = pd.DataFrame(df_hts_trips, copy=True)

        df_hts_households["hts"] = name
        df_hts_persons["hts"] = name
        df_hts_trips["hts"] = name

        if "routed_distance" in df_hts_trips:
            df_hts_trips = df_hts_trips.rename(
                columns={"routed_distance": "hts_distance"}
            )
            df_hts_trips["distance_type"] = "routed"
        elif "euclidean_distance" in df_hts_trips:
            df_hts_trips = df_hts_trips.rename(
                columns={"euclidean_distance": "hts_distance"}
            )
            df_hts_trips["distance_type"] = "euclidean"
        else:
            raise RuntimeError("No distance slot available")

        households.append(df_hts_households)
        persons.append(df_hts_persons)
        trips.append(df_hts_trips)

    return pd.concat(households), pd.concat(persons), pd.concat(trips)


def execute(context):
    egt = context.stage("data.hts.egt.filtered")
    entd = context.stage("data.hts.entd.filtered")

    htss = dict(egt=egt, entd=entd)
    names = sorted(list(htss.keys()))

    # Make data set of all HTS
    df_households, df_persons, df_trips = combine(htss)

    # Collect general count information
    info = {}
    for name in names:
        f_hts_households = df_households["hts"] == name
        f_hts_persons = df_persons["hts"] == name
        f_hts_trips = df_trips["hts"] == name
        f_any_trips = df_persons["number_of_trips"] > 0

        info[name] = {
            "number_of_households": np.count_nonzero(f_hts_households),
            "number_of_persons": np.count_nonzero(f_hts_persons),
            "number_of_trips": np.count_nonzero(f_hts_trips),
            "weighted_number_of_households": df_households[f_hts_households][
                "household_weight"
            ].sum(),
            "weighted_number_of_persons": df_persons[f_hts_persons][
                "person_weight"
            ].sum(),
            "weighted_number_of_trips": df_trips[f_hts_trips]["trip_weight"].sum(),
            "weighted_number_of_trips_per_mobile_person": (
                df_persons[f_hts_persons & f_any_trips]["number_of_trips"]
                * df_persons[f_hts_persons & f_any_trips]["trip_weight"]
            ).sum()
            / df_persons[f_hts_persons & f_any_trips]["trip_weight"].sum(),
            "share_of_students": (
                df_persons[f_hts_persons]["studies"]
                * df_persons[f_hts_persons]["person_weight"]
            ).sum()
            / df_persons[f_hts_persons]["person_weight"].sum(),
            "share_of_employed": (
                df_persons[f_hts_persons]["employed"]
                * df_persons[f_hts_persons]["person_weight"]
            ).sum()
            / df_persons[f_hts_persons]["person_weight"].sum(),
            "number_of_activity_chains": len(
                df_trips[f_hts_trips]["person_id"].unique()
            ),
            "number_of_activity_chains": len(
                df_trips[f_hts_trips]["person_id"].unique()
            ),
        }

    # Trip distance distribution
    df_trips["distance_class"] = np.digitize(
        df_trips["hts_distance"], np.arange(1, 10) * 1000
    )
    df_distance = (
        df_trips.groupby(["hts", "distance_class"])["trip_weight"]
        .sum()
        .reset_index(name="trip_weight")
    )

    # Age distribution
    AGE_BOUNDS = [14, 29, 44, 59, 74, 1000]

    df_persons["age_class"] = np.digitize(df_persons["age"], AGE_BOUNDS, right=True)
    df_age = (
        df_persons.groupby(["hts", "age_class"])["person_weight"]
        .sum()
        .reset_index(name="person_weight")
    )

    df_census = pd.DataFrame(
        context.stage("data.census.filtered")[["age", "studies", "weight", "employed"]],
        copy=True,
    )
    df_census["hts"] = "census"
    df_census["age_class"] = np.digitize(df_census["age"], AGE_BOUNDS, right=True)
    df_age_census = (
        df_census.groupby(["hts", "age_class"])["weight"]
        .sum()
        .reset_index(name="person_weight")
    )

    df_age = pd.concat([df_age, df_age_census])

    # Add student and employment share for census
    info["census"] = {
        "share_of_students": (df_census["studies"] * df_census["weight"]).sum()
        / df_census["weight"].sum(),
        "share_of_employed": (df_census["employed"] * df_census["weight"]).sum()
        / df_census["weight"].sum(),
    }

    return {
        "info": info,
        "distance_distribution": df_distance,
        "age_distribution": df_age,
    }
