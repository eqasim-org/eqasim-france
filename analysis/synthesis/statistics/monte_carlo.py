import numpy as np
import pandas as pd

import analysis.bootstrapping as bt
import analysis.marginals as marginals
import analysis.statistics as stats

SAMPLING_RATES = [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2]
ACQUISITION_SAMPLE_SIZE = 200
ERROR_THRESHOLD = 0.01

from analysis.synthesis.statistics.marginal import MARGINALS


def configure(context):
    context.stage("analysis.reference.census.sociodemographics")

    for sampling_rate in SAMPLING_RATES:
        bt.configure(
            context,
            "analysis.synthesis.statistics.marginal",
            ACQUISITION_SAMPLE_SIZE,
            dict(sampling_rate=sampling_rate),
            alias="sample_%f" % sampling_rate,
        )


STATISTICS = [
    ("mean", "mean"),
    ("q5", lambda x: x.quantile(0.05)),
    ("q95", lambda x: x.quantile(0.95)),
]

STATISTICS = {
    "weight": STATISTICS,
    "error": STATISTICS,
    "error_probability": [("mean", "mean")],
}


def process(context, k):
    reference = context.data("reference")
    partial_marginals = context.data("partial_marginals")
    sampling_rate = context.data("sampling_rate")

    k_marginals = stats.combine_marginals(partial_marginals[:k])
    output = {}

    for marginal in MARGINALS:
        df_marginal = k_marginals[marginal]
        df_reference = reference[marginal]

        df_marginal = pd.merge(
            df_marginal,
            df_reference.rename(columns={"weight": "reference"}),
            on=marginal,
        )
        df_marginal["weight"] /= sampling_rate
        df_marginal["error"] = df_marginal["weight"] / df_marginal["reference"] - 1
        df_marginal["error_probability"] = (
            np.abs(df_marginal["error"]) <= ERROR_THRESHOLD
        )

        df = (
            df_marginal[list(marginal) + ["weight", "error", "error_probability"]]
            .groupby(list(marginal))
            .aggregate(STATISTICS)
            .reset_index()
        )

        df["samples"] = k
        df["sampling_rate"] = sampling_rate

        context.progress.update()
        output[marginal] = df

    return output


def execute(context):
    reference = context.stage("analysis.reference.census.sociodemographics")["person"]

    output = {marginal: [] for marginal in MARGINALS}
    total = len(SAMPLING_RATES) * len(MARGINALS) * ACQUISITION_SAMPLE_SIZE

    with context.progress(
        label="Running Monte Carlo analysis ...", total=total
    ) as progress:
        for sampling_rate in SAMPLING_RATES:
            partial_marginals = list(
                bt.get_stages(
                    context,
                    "sample_%f" % sampling_rate,
                    sample_size=ACQUISITION_SAMPLE_SIZE,
                )
            )

            with context.parallel(
                data=dict(
                    partial_marginals=partial_marginals,
                    reference=reference,
                    sampling_rate=sampling_rate,
                )
            ) as parallel:

                for partial_output in parallel.imap_unordered(
                    process, np.arange(1, ACQUISITION_SAMPLE_SIZE + 1)
                ):
                    for marginal in MARGINALS:
                        output[marginal].append(partial_output[marginal])

    for marginal in MARGINALS:
        output[marginal] = pd.concat(output[marginal])

    return output
