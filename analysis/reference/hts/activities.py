import pandas as pd
import numpy as np


def configure(context):
    context.stage("data.hts.selected", alias="hts")


PURPOSE_MAPPING = {
    "home": "h",
    "work": "w",
    "education": "e",
    "shop": "s",
    "leisure": "l",
    "other": "o",
}


def execute(context):
    df_households, df_persons, df_activities = context.stage("hts")

    # Shift times and types of trips to arrive at activities
    df_activities["purpose"] = df_activities["preceding_purpose"]
    df_activities["end_time"] = df_activities["departure_time"]

    df_activities["start_time"] = df_activities.shift(1)["arrival_time"]
    df_activities.loc[df_activities["is_first_trip"], "start_time"] = np.nan

    df_activities["activity_id"] = df_activities["trip_id"]

    df_activities["is_first"] = df_activities["is_first_trip"]
    df_activities["is_last"] = False

    # Add missing end activity
    df_last = df_activities[df_activities["is_last_trip"]].copy()
    df_last["purpose"] = df_activities["following_purpose"]

    df_last["start_time"] = df_activities["arrival_time"]
    df_last["end_time"] = np.nan

    df_last["activity_id"] = df_activities["trip_id"] + 1

    df_last["is_first"] = False
    df_last["is_last"] = True

    df_activities = pd.concat(
        [
            df_activities[
                [
                    "person_id",
                    "activity_id",
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
                    "activity_id",
                    "purpose",
                    "start_time",
                    "end_time",
                    "is_first",
                    "is_last",
                ]
            ],
        ]
    ).sort_values(by=["person_id", "activity_id"])

    # Add activities for people without trips
    df_missing = df_persons[~df_persons["person_id"].isin(df_activities["person_id"])][
        ["person_id"]
    ]

    df_missing["activity_id"] = 0
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
