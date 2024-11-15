import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting

from .general import prepare_data, add_labels

SAMPLING_RATE = 0.05


def configure(context):
    context.stage("analysis.reference.census.sociodemographics")

    context.stage(
        "analysis.synthesis.sociodemographics.spatial",
        dict(sampling_rate=SAMPLING_RATE),
        alias="data",
    )


def filter_commune(marginals, commune_id, levels=["person", "household"]):
    result = {}

    for level in levels:
        level_result = {}

        for attributes, df_marginal in marginals[level].items():
            if "commune_id" in attributes:
                f = df_marginal["commune_id"] == str(commune_id)
                df_marginal = df_marginal[f].drop(columns=["commune_id"])

                attributes = list(attributes)
                attributes.remove("commune_id")

                level_result[tuple(attributes)] = df_marginal

        result[level] = level_result

    return result


def execute(context):
    plotting.setup()

    census = context.stage("analysis.reference.census.sociodemographics")
    data = context.stage("data")

    cases = [
        dict(commune=75113, title="13th Arrondissement"),
        dict(commune=94028, title="Alfortville"),
    ]

    plt.figure(figsize=plotting.WIDE_FIGSIZE)

    for case_index, case in enumerate(cases):
        case_census = filter_commune(census, case["commune"])
        case_data = filter_commune(data, case["commune"])

        df_case = pd.concat(
            [
                prepare_data(
                    case_data,
                    case_census,
                    case_census,
                    "household",
                    ["household_size_class"],
                    SAMPLING_RATE,
                ),
                prepare_data(
                    case_data,
                    case_census,
                    case_census,
                    "person",
                    ["age_class"],
                    SAMPLING_RATE,
                ),
            ]
        )

        add_labels(df_case)

        plt.subplot(1, 2, case_index + 1)
        locations = np.arange(len(df_case))

        reference_values = df_case["reference"].values
        mean_values = df_case["mean"].values

        plt.barh(
            locations,
            df_case["reference"].values,
            height=0.4,
            label="Census",
            align="edge",
            linewidth=0.5,
            edgecolor="white",
            color=plotting.COLORS["census"],
        )
        plt.barh(
            locations + 0.4,
            df_case["mean"].values,
            height=0.4,
            label="Synthetic",
            align="edge",
            linewidth=0.5,
            edgecolor="white",
            color=plotting.COLORS["synthetic"],
        )

        for index, (min, max) in enumerate(
            zip(df_case["min"].values, df_case["max"].values)
        ):
            location = index + 0.4 + 0.2
            plt.plot([min, max], [location, location], "k", linewidth=1, label="Range")

        plt.gca().yaxis.set_major_locator(tck.FixedLocator(locations + 0.4))

        if case_index == 0:
            plt.gca().yaxis.set_major_formatter(
                tck.FixedFormatter(df_case["label"].values)
            )
        else:
            plt.gca().yaxis.set_major_formatter(tck.FixedFormatter([""] * 100))

        plt.gca().xaxis.set_major_formatter(
            tck.FuncFormatter(lambda x, p: "%dk" % (x // 1000,))
        )

        plt.grid()
        plt.gca().set_axisbelow(True)
        plt.gca().yaxis.grid(alpha=0.0)
        plt.gca().invert_yaxis()

        plt.xlabel("Number of persons / households")
        plt.title(case["title"])
        # plt.ylim([len(locations) + 2.5, -0.5])

        if case_index == 1:
            handles, labels = plt.gca().get_legend_handles_labels()
            handles = [handles[-2], handles[-1], handles[-3]]
            labels = [labels[-2], labels[-1], labels[-3]]
            plt.legend(handles=handles, labels=labels, loc=(0.05, 0.32), framealpha=1.0)

    plt.tight_layout()
    plt.savefig("%s/comparison.pdf" % (context.path(),))
    plt.close()
