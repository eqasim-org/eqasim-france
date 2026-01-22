import pandas as pd
import numpy as np

def configure(context):
    context.stage("data.hts.selected")

def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.selected")
    df = pd.merge(df_trips, df_persons[["person_id", "person_weight"]])

    df["distance"] = df["euclidean_distance"]
    df["travel_time"] = df["arrival_time"] - df["departure_time"]

    primary_activities = ["home", "work", "education"]
    #primary_activities = []
    df = df[~(
        df["preceding_purpose"].isin(primary_activities) &
        df["following_purpose"].isin(primary_activities)
    )]

    data = dict()

    for mode in ["car", "car_passenger", "pt", "bicycle", "walk"]:
        f = df["mode"] == mode

        if np.count_nonzero(f) > 0:
            values = df[f]["distance"].values
            weights = df[f]["person_weight"].values

            sorter = np.argsort(values)
            values = values[sorter]
            cdf = np.cumsum(weights[sorter])
            cdf /= cdf[-1]

            data[mode] = dict(values = values, cdf = cdf)

    return data
