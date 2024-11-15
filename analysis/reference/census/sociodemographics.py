import analysis.statistics as stats
import analysis.marginals as marginals


def configure(context):
    context.stage("data.census.filtered")


def execute(context):
    person_marginals = marginals.combine(
        marginals.TOTAL_MARGINAL,
        marginals.CENSUS_PERSON_MARGINALS,
        marginals.CENSUS_HOUSEHOLD_MARGINALS,
        marginals.cross(
            marginals.CENSUS_PERSON_MARGINALS, marginals.CENSUS_PERSON_MARGINALS
        ),
        marginals.cross(
            marginals.CENSUS_HOUSEHOLD_MARGINALS, marginals.CENSUS_HOUSEHOLD_MARGINALS
        ),
        marginals.cross(
            marginals.CENSUS_PERSON_MARGINALS, marginals.CENSUS_HOUSEHOLD_MARGINALS
        ),
        marginals.SPATIAL_MARGINALS,
        marginals.cross(marginals.SPATIAL_MARGINALS, marginals.CENSUS_PERSON_MARGINALS),
    )

    household_marginals = marginals.combine(
        marginals.TOTAL_MARGINAL,
        marginals.CENSUS_HOUSEHOLD_MARGINALS,
        marginals.cross(
            marginals.CENSUS_HOUSEHOLD_MARGINALS, marginals.CENSUS_HOUSEHOLD_MARGINALS
        ),
        marginals.SPATIAL_MARGINALS,
        marginals.cross(
            marginals.SPATIAL_MARGINALS, marginals.CENSUS_HOUSEHOLD_MARGINALS
        ),
    )

    df_persons = context.stage("data.census.filtered")
    marginals.prepare_classes(df_persons)

    df_households = df_persons.drop_duplicates("household_id").copy()

    return dict(
        person=stats.marginalize(df_persons, person_marginals),
        household=stats.marginalize(df_households, household_marginals),
    )
