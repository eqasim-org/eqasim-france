import gzip
from tqdm import tqdm
import pandas as pd
import numpy as np

"""
Transforms the synthetic trip table into a synthetic activity table.
"""


def configure(context):
    context.stage("synthesis.population.enriched")
    context.stage("synthesis.population.trips")


def execute(context):
    df_activities = context.stage("synthesis.population.trips")

    # Add trip count
    counts = (
        df_activities.groupby("person_id")
        .size()
        .reset_index(name="trip_count")["trip_count"]
        .values
    )
    df_activities["trip_count"] = np.hstack([[count] * count for count in counts])

    # Shift times and types of trips to arrive at activities
    df_activities["purpose"] = df_activities["preceding_purpose"]
    df_activities["end_time"] = df_activities["departure_time"]

    df_activities["start_time"] = df_activities.shift(1)["arrival_time"]
    df_activities.loc[df_activities["is_first_trip"], "start_time"] = np.nan

    df_activities["is_first"] = df_activities["is_first_trip"]
    df_activities["is_last"] = False

    df_activities["activity_index"] = df_activities["trip_index"]

    # Add missing end activity
    df_last = df_activities[df_activities["is_last_trip"]].copy()
    df_last["purpose"] = df_activities["following_purpose"]

    df_last["start_time"] = df_activities["arrival_time"]
    df_last["end_time"] = np.nan

    df_last["is_first"] = False
    df_last["is_last"] = True

    df_last["activity_index"] = df_last["trip_count"]
    df_last["trip_index"] = -1

    df_activities = pd.concat(
        [
            df_activities[
                [
                    "person_id",
                    "activity_index",
                    "trip_index",
                    "purpose",
                    "start_time",
                    "end_time",
                    "is_first",
                    "is_last",
                ]
            ],
            df_last[
                [
                    "person_id",
                    "activity_index",
                    "trip_index",
                    "purpose",
                    "start_time",
                    "end_time",
                    "is_first",
                    "is_last",
                ]
            ],
        ]
    ).sort_values(by=["person_id", "activity_index"])

    # Add activities for people without trips
    df_missing = context.stage("synthesis.population.enriched")
    df_missing = df_missing[~df_missing["person_id"].isin(df_activities["person_id"])][
        ["person_id"]
    ]

    df_missing["activity_index"] = 0
    df_missing["trip_index"] = -1
    df_missing["purpose"] = "home"
    df_missing["start_time"] = np.nan
    df_missing["end_time"] = np.nan
    df_missing["is_first"] = True
    df_missing["is_last"] = True

    df_missing["purpose"] = df_missing["purpose"].astype(df_activities["purpose"].dtype)
    df_activities = pd.concat([df_activities, df_missing])

    # Some cleanup
    df_activities["duration"] = df_activities["end_time"] - df_activities["start_time"]

    return df_activities
