import pandas as pd
import numpy as np


def configure(context):
    context.config("random_seed")
    context.stage("data.hts.selected")


def get_commuting_distance(df_persons, df_trips, activity_type, random):
    if "euclidean_distance" in df_trips:
        distance_slot = "euclidean_distance"
        distance_factor = 1.0
    else:
        distance_slot = "routed_distance"
        distance_factor = 1.0  # / 1.3

    # Add commuting distances
    df_commute_distance = (
        df_trips[
            (
                (df_trips["preceding_purpose"] == "home")
                & (df_trips["following_purpose"] == activity_type)
            )
            | (
                (df_trips["preceding_purpose"] == activity_type)
                & (df_trips["following_purpose"] == "home")
            )
        ]
        .drop_duplicates("person_id", keep="first")[["person_id", distance_slot]]
        .rename(columns={distance_slot: "commute_distance"})
    )

    df_persons = pd.merge(df_persons, df_commute_distance, on="person_id", how="left")

    # For the ones without commuting distance, sample from the distribution
    f_missing = df_persons["commute_distance"].isna()

    # TODO: We can impute distances here by mode, which would make it more consistent!
    # Also, we could make the OD matrices by mode.

    values = df_persons["commute_distance"][~f_missing].values
    weights = df_persons["person_weight"][~f_missing].values

    sorter = np.argsort(values)
    values = values[sorter]
    weights = weights[sorter]

    cdf = np.cumsum(weights)
    cdf /= cdf[-1]

    indices = [
        np.searchsorted(cdf, r)
        for r in random.random_sample(size=np.count_nonzero(f_missing))
    ]

    df_persons.loc[f_missing, "commute_distance"] = values[indices]

    # Set flag for reference
    df_persons["imputed"] = f_missing

    # Attach euclidean factor
    df_persons["commute_distance"] *= distance_factor

    print(
        "Missing %s commute distances: %.2f%%"
        % (activity_type, 100 * np.count_nonzero(f_missing) / len(f_missing))
    )

    return df_persons


def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.selected")
    random = np.random.RandomState(context.config("random_seed"))

    return dict(
        work=get_commuting_distance(df_persons, df_trips, "work", random),
        education=get_commuting_distance(df_persons, df_trips, "education", random),
    )
