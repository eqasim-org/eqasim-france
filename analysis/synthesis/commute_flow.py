import pandas as pd
import numpy as np

import analysis.bootstrapping as bs
import analysis.statistics as stats
import analysis.marginals as marginals


def configure(context):
    acquisition_sample_size = context.config("acquisition_sample_size")

    bs.configure(
        context, "synthesis.population.spatial.home.zones", acquisition_sample_size
    )
    bs.configure(
        context,
        "synthesis.population.spatial.primary.locations",
        acquisition_sample_size,
    )
    bs.configure(context, "synthesis.population.sampled", acquisition_sample_size)

    context.stage("data.spatial.municipalities")


def execute(context):
    df_codes = context.stage("data.spatial.municipalities")[
        ["commune_id", "departement_id"]
    ]

    acquisition_sample_size = context.config("acquisition_sample_size")

    feeder = zip(
        bs.get_stages(
            context, "synthesis.population.spatial.home.zones", acquisition_sample_size
        ),
        bs.get_stages(
            context,
            "synthesis.population.spatial.primary.locations",
            acquisition_sample_size,
        ),
        bs.get_stages(context, "synthesis.population.sampled", acquisition_sample_size),
    )

    work_flows = []
    education_flows = []

    with context.progress(
        label="Processing commute data ...", total=acquisition_sample_size
    ) as progress:
        for realization, (df_home, df_spatial, df_persons) in enumerate(feeder):
            # Prepare home
            df_home = pd.merge(
                df_persons[["person_id", "household_id"]], df_home, on="household_id"
            )
            df_home = df_home[["person_id", "departement_id"]].rename(
                columns={"departement_id": "home"}
            )

            # Prepare work
            df_work = df_spatial[0]
            df_work = pd.merge(df_work, df_codes, how="left", on="commune_id")
            df_work["departement_id"] = df_work[
                "departement_id"
            ].cat.remove_unused_categories()
            df_work = df_work[["person_id", "departement_id"]].rename(
                columns={"departement_id": "work"}
            )

            # Calculate work
            df_work = (
                pd.merge(df_home, df_work, on="person_id")
                .groupby(["home", "work"])
                .size()
                .reset_index(name="weight")
            )
            df_work["realization"] = realization
            work_flows.append(df_work)

            # Prepare work
            df_education = df_spatial[1]
            df_education = pd.merge(df_education, df_codes, how="left", on="commune_id")
            df_education["departement_id"] = df_education[
                "departement_id"
            ].cat.remove_unused_categories()
            df_education = df_education[["person_id", "departement_id"]].rename(
                columns={"departement_id": "education"}
            )

            # Calculate education
            df_education = (
                pd.merge(df_home, df_education, on="person_id")
                .groupby(["home", "education"])
                .size()
                .reset_index(name="weight")
            )
            df_education["realization"] = realization
            education_flows.append(df_education)

            progress.update()

    df_work = pd.concat(work_flows)
    df_education = pd.concat(education_flows)

    df_work = stats.analyze_sample_and_flatten(df_work)
    df_education = stats.analyze_sample_and_flatten(df_education)

    return dict(work=df_work, education=df_education)
