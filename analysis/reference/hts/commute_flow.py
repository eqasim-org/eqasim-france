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

    df_trips = context.stage("hts")[2][
        [
            "person_id",
            "origin_departement_id",
            "destination_departement_id",
            "preceding_purpose",
            "following_purpose",
        ]
    ]

    # Prepare homes
    df_homes = (
        df_trips[df_trips["preceding_purpose"] == "home"][
            ["person_id", "origin_departement_id"]
        ]
        .rename(columns={"origin_departement_id": "home"})
        .drop_duplicates("person_id")
    )

    # Calculate work
    df_work = (
        df_trips[df_trips["following_purpose"] == "work"][
            ["person_id", "destination_departement_id"]
        ]
        .rename(columns={"destination_departement_id": "work"})
        .drop_duplicates("person_id")
    )

    df_work = pd.merge(df_homes, df_work, on="person_id")
    df_work = pd.merge(df_work, df_weight, on="person_id", how="left")

    df_work = df_work.groupby(["home", "work"])["weight"].sum()
    df_work = df_work.reset_index()

    # Calculate education
    df_education = (
        df_trips[df_trips["following_purpose"] == "education"][
            ["person_id", "destination_departement_id"]
        ]
        .rename(columns={"destination_departement_id": "education"})
        .drop_duplicates("person_id")
    )

    df_education = pd.merge(df_homes, df_education, on="person_id")
    df_education = pd.merge(df_education, df_weight, on="person_id", how="left")

    df_education = df_education.groupby(["home", "education"])["weight"].sum()
    df_education = df_education.reset_index()

    # Calculate corrections for employed non-movers
    df_existing = context.stage("hts")[1][
        ["employed", "departement_id", "person_weight"]
    ].rename(columns={"person_weight": "weight", "departement_id": "home"})
    df_existing = df_existing[df_existing["employed"]]
    df_existing = (
        df_existing.groupby("home")["weight"]
        .sum()
        .reset_index()
        .rename(columns={"weight": "existing"})
    )

    df_origin = (
        df_work.groupby("home")["weight"]
        .sum()
        .reset_index()
        .rename(columns={"weight": "active"})
    )

    df_work_correction = pd.merge(df_existing, df_origin, on="home")
    df_work_correction["factor"] = (
        df_work_correction["active"] / df_work_correction["existing"]
    )
    df_work_correction = df_work_correction[["home", "factor"]]

    # Calculate corrections for studying non-movers
    df_existing = context.stage("hts")[1][
        ["studies", "departement_id", "person_weight"]
    ].rename(columns={"person_weight": "weight", "departement_id": "home"})
    df_existing = df_existing[df_existing["studies"]]
    df_existing = (
        df_existing.groupby("home")["weight"]
        .sum()
        .reset_index()
        .rename(columns={"weight": "existing"})
    )

    df_origin = (
        df_education.groupby("home")["weight"]
        .sum()
        .reset_index()
        .rename(columns={"weight": "active"})
    )

    df_education_correction = pd.merge(df_existing, df_origin, on="home")
    df_education_correction["factor"] = (
        df_education_correction["active"] / df_education_correction["existing"]
    )
    df_education_correction = df_education_correction[["home", "factor"]]

    return dict(work=df_work, education=df_education), dict(
        work=df_work_correction, education=df_education_correction
    )
