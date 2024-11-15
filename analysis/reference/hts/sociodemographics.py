import analysis.statistics as stats
import analysis.marginals as marginals
import pandas as pd


def configure(context):
    context.stage("data.hts.selected", alias="hts")


def execute(context):
    df_households, df_persons, _ = context.stage("hts")

    person_columns = set(df_persons.columns)
    household_columns = set(df_households.columns)
    household_columns -= person_columns
    household_columns.add("household_id")

    df = pd.merge(df_persons, df_households[household_columns], on="household_id")
    assert len(df_persons) == len(df)
    df_persons = df

    spatial_marginals = [("departement_id",)]

    person_marginals = marginals.combine(
        marginals.TOTAL_MARGINAL,
        marginals.HTS_PERSON_MARGINALS,
        marginals.HTS_HOUSEHOLD_MARGINALS,
        marginals.cross(marginals.HTS_PERSON_MARGINALS, marginals.HTS_PERSON_MARGINALS),
        marginals.cross(
            marginals.HTS_HOUSEHOLD_MARGINALS, marginals.HTS_HOUSEHOLD_MARGINALS
        ),
        marginals.cross(
            marginals.HTS_PERSON_MARGINALS, marginals.HTS_HOUSEHOLD_MARGINALS
        ),
        spatial_marginals,
        marginals.cross(spatial_marginals, marginals.HTS_PERSON_MARGINALS),
    )

    household_marginals = marginals.combine(
        marginals.TOTAL_MARGINAL,
        marginals.HTS_HOUSEHOLD_MARGINALS,
        marginals.cross(
            marginals.HTS_HOUSEHOLD_MARGINALS, marginals.HTS_HOUSEHOLD_MARGINALS
        ),
        spatial_marginals,
        marginals.cross(spatial_marginals, marginals.HTS_HOUSEHOLD_MARGINALS),
    )

    marginals.prepare_classes(df_persons)
    df_households = df_persons.drop_duplicates("household_id").copy()

    df_persons = df_persons.rename(columns={"person_weight": "weight"})
    df_households = df_households.rename(columns={"household_weight": "weight"})

    return dict(
        person=stats.marginalize(df_persons, person_marginals),
        household=stats.marginalize(df_households, household_marginals),
    )
