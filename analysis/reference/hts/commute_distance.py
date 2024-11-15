import pandas as pd
import numpy as np

import analysis.bootstrapping as bs
import analysis.statistics as stats
import analysis.marginals as marginals


def configure(context):
    context.stage("data.hts.selected", alias="hts")


def execute(context):
    df_weight = context.stage("hts")[1][["person_id", "person_weight"]].rename(
        columns={"person_weight": "weight"}
    )
    df_trips = pd.merge(context.stage("hts")[2], df_weight, on="person_id")

    # Prepare data frames
    df_work = df_trips[
        (
            (df_trips["preceding_purpose"] == "home")
            & (df_trips["following_purpose"] == "work")
        )
        | (
            (df_trips["preceding_purpose"] == "work")
            & (df_trips["following_purpose"] == "home")
        )
    ].drop_duplicates("person_id", keep="first")[["euclidean_distance", "weight"]]

    df_education = df_trips[
        (
            (df_trips["preceding_purpose"] == "home")
            & (df_trips["following_purpose"] == "education")
        )
        | (
            (df_trips["preceding_purpose"] == "education")
            & (df_trips["following_purpose"] == "home")
        )
    ].drop_duplicates("person_id", keep="first")[["euclidean_distance", "weight"]]

    # Prepare distributions
    df_work = df_work.sort_values(by="euclidean_distance")
    df_work["cdf"] = np.cumsum(df_work["weight"])
    df_work["cdf"] /= df_work["cdf"].max()
    df_work = df_work[["euclidean_distance", "cdf"]]

    df_education = df_education.sort_values(by="euclidean_distance")
    df_education["cdf"] = np.cumsum(df_education["weight"])
    df_education["cdf"] /= df_education["cdf"].max()
    df_education = df_education[["euclidean_distance", "cdf"]]

    return dict(work=df_work, education=df_education)
