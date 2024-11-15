import analysis.bootstrapping as bs
import analysis.statistics as stats
import analysis.marginals as marginals


def configure(context):
    acquisition_sample_size = context.config("acquisition_sample_size")
    bs.configure(context, "synthesis.population.enriched", acquisition_sample_size)


def execute(context):
    acquisition_sample_size = context.config("acquisition_sample_size")

    person_marginals = []
    household_marginals = []

    for df in bs.get_stages(
        context, "synthesis.population.enriched", acquisition_sample_size
    ):
        marginals.prepare_classes(df)

        person_marginals.append(
            stats.marginalize(
                df, marginals.ANALYSIS_PERSON_MARGINALS, weight_column=None
            )
        )
        household_marginals.append(
            stats.marginalize(
                df.drop_duplicates("household_id"),
                marginals.ANALYSIS_HOUSEHOLD_MARGINALS,
                weight_column=None,
            )
        )

    person_marginals = stats.combine_marginals(person_marginals)
    household_marginals = stats.combine_marginals(household_marginals)

    person_marginals = stats.apply_per_marginal(
        person_marginals, stats.analyze_sample_and_flatten
    )
    household_marginals = stats.apply_per_marginal(
        household_marginals, stats.analyze_sample_and_flatten
    )

    return dict(person=person_marginals, household=household_marginals)
