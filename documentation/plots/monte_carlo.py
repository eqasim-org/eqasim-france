import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting

from analysis.synthesis.statistics.marginal import MARGINALS
from analysis.synthesis.statistics.monte_carlo import SAMPLING_RATES
from analysis.synthesis.statistics.monte_carlo import ACQUISITION_SAMPLE_SIZE


def configure(context):
    context.stage("analysis.reference.census.sociodemographics")
    context.stage("analysis.synthesis.statistics.monte_carlo")


SELECTED_MARGINAL = ("age_class", "employed")
SELECTED_VALUES = (3, True)

TABLE_MARGINALS = [
    "age_class",
    "employed",
    "sex",
    "socioprofessional_class",
    "studies",
]

ADDITIONAL_VALUES = [(3, True), (4, True), (5, True)]

from analysis.marginals import AGE_CLASS_LABELS

ADDITIONAL_LABELS = AGE_CLASS_LABELS[3:6]


def select(reference, data, marginal, values):
    df_marginal = data[marginal]
    df_reference = reference[marginal]

    for marginal, value in zip(marginal, values):
        df_marginal = df_marginal[df_marginal[marginal] == value]
        df_reference = df_reference[df_reference[marginal] == value]

    reference_value = df_reference["weight"].values[0]

    return df_marginal, reference_value


def execute(context):
    data = context.stage("analysis.synthesis.statistics.monte_carlo")

    # Prepare data for error probability table
    df_table = []

    for marginal in TABLE_MARGINALS:
        df_marginal = data[(marginal,)]
        values = np.sort(df_marginal[(marginal,)].drop_duplicates().values)

        for value in values:
            row = {"marginal": marginal, "value": value}

            df_value = df_marginal[df_marginal[marginal] == value]
            df_value = df_value[df_value["samples"] == ACQUISITION_SAMPLE_SIZE]

            assert len(df_value) == len(SAMPLING_RATES)
            probabilities = df_value.sort_values(by=["sampling_rate", "samples"])[
                "error_probability"
            ].values[:, 0]

            for sampling_rate, probability in zip(SAMPLING_RATES, probabilities):
                row[sampling_rate] = probability

            df_table.append(row)

    df_table = pd.DataFrame.from_records(df_table)
    df_table = create_table(df_table)
    df_table.to_latex("%s/monte_carlo_table.tex" % context.path(), escape=False)

    # Prepare data for plotting
    reference = context.stage("analysis.reference.census.sociodemographics")["person"]

    # Perform plotting
    plotting.setup()

    plt.figure(figsize=plotting.WIDE_FIGSIZE)

    # ... subplot on nominal stratum values
    plt.subplot(1, 2, 1)
    plt.title("(a) Monte Carlo analysis", fontsize=plotting.FONT_SIZE)

    df_marginal, reference_value = select(
        reference, data, SELECTED_MARGINAL, SELECTED_VALUES
    )
    assert len(df_marginal) == ACQUISITION_SAMPLE_SIZE * len(SAMPLING_RATES)

    display_sampling_rates = [0.001, 0.01, 0.05]

    for index, sampling_rate in enumerate([0.001, 0.01, 0.05]):
        df_rate = df_marginal[df_marginal["sampling_rate"] == sampling_rate]
        df_rate = df_rate.sort_values(by="samples")
        plt.fill_between(
            df_rate["samples"],
            df_rate[("weight", "q5")],
            df_rate[("weight", "q95")],
            alpha=0.25 + index * 0.2,
            color=plotting.COLORSET[0],
            linewidth=0.0,
        )

    plt.plot(
        [1, ACQUISITION_SAMPLE_SIZE],
        [reference_value] * 2,
        "k--",
        label="Ref. $y$",
        linewidth=1.0,
    )
    plt.plot(
        [1, ACQUISITION_SAMPLE_SIZE],
        [reference_value * 0.99] * 2,
        "k:",
        label="1% Err.",
        linewidth=1.0,
    )
    plt.plot(
        [1, ACQUISITION_SAMPLE_SIZE], [reference_value * 1.01] * 2, "k:", linewidth=1.0
    )

    plt.xlabel("Sample size $N$")
    plt.ylabel("Stratum weight")

    plt.gca().yaxis.set_major_formatter(
        tck.FuncFormatter(lambda x, p: "%.2fM" % (x * 1e-6,))
    )

    plt.grid()
    plt.gca().set_axisbelow(True)
    plt.xlim([1, ACQUISITION_SAMPLE_SIZE])

    plt.fill_between(
        [np.nan],
        [np.nan],
        [np.nan],
        color=plotting.COLORSET[0],
        alpha=0.25,
        label="90% Conf.",
    )
    plt.legend(loc="lower center", ncol=2)

    # ... subplot on nominal stratum values
    plt.subplot(1, 2, 2)
    plt.title("(b) Error probability", fontsize=plotting.FONT_SIZE)

    for index, values in enumerate(ADDITIONAL_VALUES):
        df_marginal, reference_value = select(
            reference, data, SELECTED_MARGINAL, values
        )
        assert len(df_marginal) == ACQUISITION_SAMPLE_SIZE * len(SAMPLING_RATES)

        df_max = df_marginal[df_marginal["samples"] == ACQUISITION_SAMPLE_SIZE]
        df_max = df_max.sort_values(by="sampling_rate")

        plt.plot(
            100 * np.array(SAMPLING_RATES),
            df_max[("error_probability", "mean")],
            color=plotting.COLORSET[index],
            label="Age %s" % ADDITIONAL_LABELS[index],
            marker=".",
            markersize=3.0,
            linewidth=1.0,
        )

    plt.plot(
        [0, 100 * max(SAMPLING_RATES)],
        [0.9] * 2,
        "k:",
        label="90% Prob.",
        linewidth=1.0,
    )
    plt.xlim([0, 100 * max(SAMPLING_RATES)])
    plt.ylim([0, 1.0])

    plt.xlabel("Sampling rate $s$ [%]")
    plt.ylabel("Error probability")

    plt.grid()
    plt.gca().set_axisbelow(True)

    plt.legend(loc="center", ncol=1)

    plt.tight_layout()
    plt.savefig("%s/monte_carlo.pdf" % context.path())
    plt.close()


import analysis.marginals


def label_row(row):
    if row["marginal"] == "age_class":
        return analysis.marginals.AGE_CLASS_LABELS[row["value"]]

    elif row["marginal"] == "sex":
        return row["value"].capitalize()

    elif row["marginal"] == "employed":
        return "Employed" if row["value"] else "Unemployed"

    elif row["marginal"] == "studies":
        return "Yes" if row["value"] else "No"

    elif row["marginal"] == "socioprofessional_class":
        return analysis.marginals.SOCIOPROFESIONAL_CLASS_LABELS[row["value"]]


def bold_probability(x):
    if x >= 0.9:
        return "\\textbf{%.2f}" % x
    else:
        return "%.2f" % x


def create_table(df_table):
    df_table["value"] = df_table.apply(label_row, axis=1, raw=False)

    df_table["marginal"] = df_table["marginal"].map(
        {
            "age_class": "Age",
            "sex": "Sex",
            "employed": "Employed",
            "studies": "Studies",
            "socioprofessional_class": "Socioprof. Cat.",
        }
    )

    for sampling_rate in SAMPLING_RATES:
        df_table[sampling_rate] = df_table[sampling_rate].apply(bold_probability)

    df_table.columns = ["Variable", "Stratum"] + [
        "%.1f%%" % (100 * s,) for s in SAMPLING_RATES
    ]
    df_table = df_table.set_index(["Variable", "Stratum"])
    df_table.columns = pd.MultiIndex.from_tuples(
        [("Sampling rate $s$", str(s)) for s in SAMPLING_RATES]
    )

    return df_table
