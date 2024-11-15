import pandas as pd
import numpy as np

import analysis.bootstrapping as bs
import analysis.statistics as stats
import analysis.marginals as marginals

from analysis.chains import (
    aggregate_chains,
    CHAIN_MARGINALS,
    CHAIN_LENGTH_LIMIT,
    CHAIN_TOP_K,
)


def configure(context):
    acquisition_sample_size = context.config("acquisition_sample_size")

    bs.configure(context, "synthesis.population.sampled", acquisition_sample_size)
    bs.configure(context, "synthesis.population.activities", acquisition_sample_size)


def execute_parallel(context, data):
    acquisition_sample_size = context.config("acquisition_sample_size")
    df_population, df_chains = data

    df_chains = df_chains[["person_id", "activity_index", "purpose"]].sort_values(
        by=["person_id", "activity_index"]
    )
    df_chains = aggregate_chains(df_chains)

    marginals.prepare_classes(df_population)
    df_chains = pd.merge(
        df_population[["person_id", "age_class", "sex", "age"]],
        df_chains,
        on="person_id",
    )
    df_chains["chain_length_class"] = np.minimum(
        df_chains["chain_length"], CHAIN_LENGTH_LIMIT
    )

    top_k_chains = (
        df_chains.groupby("chain")
        .size()
        .reset_index(name="weight")
        .sort_values(by="weight", ascending=False)
        .head(CHAIN_TOP_K)["chain"]
        .values
    )
    df_chains = df_chains[df_chains["chain"].isin(top_k_chains)]

    df_chains["age_range"] = (df_chains["age"] >= 18) & (df_chains["age"] <= 40)

    context.progress.update()
    return stats.marginalize(df_chains, CHAIN_MARGINALS, weight_column=None)


def execute(context):
    acquisition_sample_size = context.config("acquisition_sample_size")

    data = []

    feeder = zip(
        bs.get_stages(context, "synthesis.population.sampled", acquisition_sample_size),
        bs.get_stages(
            context, "synthesis.population.activities", acquisition_sample_size
        ),
    )

    with context.progress(
        label="Marginalizing chain data ...", total=acquisition_sample_size
    ):
        with context.parallel() as parallel:
            data = list(parallel.imap_unordered(execute_parallel, feeder))

    data = stats.combine_marginals(data)
    data = stats.apply_per_marginal(data, stats.analyze_sample_and_flatten)

    return data
