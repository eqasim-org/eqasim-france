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
    context.stage("analysis.reference.hts.activities")
    context.stage("data.hts.selected", alias="hts")


def execute(context):
    df_chains = context.stage("analysis.reference.hts.activities")[
        ["person_id", "activity_id", "purpose"]
    ].sort_values(by=["person_id", "activity_id"])
    df_chains = aggregate_chains(df_chains)

    df_population = context.stage("hts")[1]
    marginals.prepare_classes(df_population)

    df_chains = pd.merge(
        df_population[["person_id", "age_class", "sex", "person_weight", "age"]],
        df_chains,
        on="person_id",
    )
    df_chains["chain_length_class"] = np.minimum(
        df_chains["chain_length"], CHAIN_LENGTH_LIMIT
    )

    top_k_chains = (
        df_chains.groupby("chain")["person_weight"]
        .sum()
        .reset_index()
        .sort_values(by="person_weight", ascending=False)
        .head(CHAIN_TOP_K)["chain"]
        .values
    )
    df_chains = df_chains[df_chains["chain"].isin(top_k_chains)]

    df_chains["age_range"] = (df_chains["age"] >= 18) & (df_chains["age"] <= 40)

    return stats.marginalize(df_chains, CHAIN_MARGINALS, weight_column="person_weight")
