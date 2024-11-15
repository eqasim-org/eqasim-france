import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting

SAMPLING_RATE = 0.05


def configure(context):
    context.stage("analysis.reference.hts.commute_distance", alias="hts")
    context.stage(
        "analysis.synthesis.commute_distance",
        dict(sampling_rate=SAMPLING_RATE),
        alias="data",
    )
    context.stage("analysis.reference.od.commute_distance", alias="census")
    context.config("hts")


def execute(context):
    plotting.setup()

    hts_data = context.stage("hts")
    data = context.stage("data")
    census_data = context.stage("census")
    hts_name = context.config("hts")

    plt.figure(figsize=plotting.SHORT_FIGSIZE)

    parts = [
        {"slot": "work", "linestyle": "-", "title": "Work"},
        {"slot": "education", "linestyle": "--", "title": "Educ."},
    ]

    for part in parts:
        slot = part["slot"]

        # plt.plot(census_data[slot]["centroid_distance"] * 1e-3, census_data[slot]["cdf"], color = plotting.COLORS["census"], linestyle = part["linestyle"], linewidth = 1.0)

        plt.plot(
            data[slot]["mean"],
            data[slot]["cdf"],
            color="k",
            linestyle=part["linestyle"],
            linewidth=1.0,
        )
        plt.fill_betweenx(
            data[slot]["cdf"],
            data[slot]["min"],
            data[slot]["max"],
            color="k",
            linewidth=0.0,
            alpha=0.25,
        )

        plt.plot(
            hts_data[slot]["euclidean_distance"] * 1e-3,
            hts_data[slot]["cdf"],
            color=plotting.COLORS[hts_name],
            linestyle=part["linestyle"],
            linewidth=1.0,
        )

        plt.plot(
            [np.nan],
            color="k",
            linewidth=1.0,
            linestyle=part["linestyle"],
            label=part["title"],
        )

    plt.plot([np.nan], color="k", linewidth=1.0, label="Synthetic")
    plt.plot([np.nan], color=plotting.COLORS[hts_name], linewidth=1.0, label="HTS")

    plt.xlim([0, 40])
    plt.ylim([0, 1])

    plt.legend(loc="best", ncol=2)

    plt.grid()
    plt.gca().set_axisbelow(True)

    plt.xlabel("Euclidean commute distance [km]")
    plt.ylabel("Cumulative density")

    plt.tight_layout()
    plt.savefig("%s/commute_distance_cdf.pdf" % context.path())
    plt.close()
