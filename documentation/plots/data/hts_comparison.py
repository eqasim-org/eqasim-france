import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as tck

import documentation.plotting as plotting


def configure(context):
    context.stage("data.hts.comparison")


def execute(context):
    plotting.setup()

    hts_comparison = context.stage("data.hts.comparison")

    # Distance distribution plot
    df_distance = hts_comparison["distance_distribution"]

    f_entd = df_distance["hts"] == "entd"
    f_egt = df_distance["hts"] == "egt"

    plt.figure()

    plt.bar(
        df_distance[f_entd]["distance_class"].values,
        df_distance[f_entd]["trip_weight"].values / 1e6,
        width=0.4,
        label="ENTD (Routed)",
        align="edge",
        color=plotting.COLORS["entd"],
        linewidth=0.5,
        edgecolor="white",
    )
    plt.bar(
        df_distance[f_egt]["distance_class"].values + 0.4,
        df_distance[f_egt]["trip_weight"].values / 1e6,
        width=0.4,
        label="EGT (Euclidean)",
        align="edge",
        color=plotting.COLORS["egt"],
        linewidth=0.5,
        edgecolor="white",
    )

    plt.gca().xaxis.set_major_locator(tck.FixedLocator(np.arange(0, 10, 2) + 0.4))
    plt.gca().xaxis.set_major_formatter(
        tck.FixedFormatter(["<%dkm" % d for d in np.arange(1, 10, 2)])
    )

    plt.gca().annotate(r"≥10 km", xy=(10.0, 8.0), xycoords="data", ha="right")

    plt.grid()
    plt.gca().set_axisbelow(True)
    plt.gca().xaxis.grid(alpha=0.0)

    plt.xlabel("Trip distance")
    plt.ylabel("Number of trips [$10^6$]")

    plt.legend()

    plt.tight_layout()
    plt.savefig("%s/distance_distribution.pdf" % context.path())
    plt.close()

    # HTS Age distribution plot
    df_age = hts_comparison["age_distribution"]

    f_entd = df_age["hts"] == "entd"
    f_egt = df_age["hts"] == "egt"
    f_census = df_age["hts"] == "census"

    plt.figure()

    plt.bar(
        df_age[f_census]["age_class"].values,
        df_age[f_census]["person_weight"].values / 1e6,
        width=0.25,
        label="Census",
        align="edge",
        color=plotting.COLORS["census"],
        linewidth=0.5,
        edgecolor="white",
    )
    plt.bar(
        df_age[f_entd]["age_class"].values + 0.25,
        df_age[f_entd]["person_weight"].values / 1e6,
        width=0.25,
        label="ENTD",
        align="edge",
        color=plotting.COLORS["entd"],
        linewidth=0.5,
        edgecolor="white",
    )
    plt.bar(
        df_age[f_egt]["age_class"].values + 0.5,
        df_age[f_egt]["person_weight"].values / 1e6,
        width=0.25,
        label="EGT",
        align="edge",
        color=plotting.COLORS["egt"],
        linewidth=0.5,
        edgecolor="white",
    )

    plt.gca().xaxis.set_major_locator(tck.FixedLocator(np.arange(1000) + 0.75 / 2))
    plt.gca().xaxis.set_major_formatter(
        tck.FixedFormatter(["%d0s" % d for d in np.arange(1, 10, 2)])
    )

    AGE_BOUNDS = ["<15", "15-29", "30-44", "45-59", "60-74", ">75"]
    plt.gca().xaxis.set_major_formatter(tck.FixedFormatter(AGE_BOUNDS))

    plt.gca().annotate(
        "A",
        xy=(1.5 + 0.5 * 0.25, 2.0),
        xycoords="data",
        xytext=(1.5 + 0.5 * 0.25, 2.35),
        textcoords="data",
        arrowprops={"arrowstyle": "-|>", "facecolor": "black", "linewidth": 0.5},
        bbox={"pad": 0.0, "linewidth": 0.0, "facecolor": (1.0, 0.0, 0.0, 0.0)},
        ha="center",
    )

    plt.gca().annotate(
        "B",
        xy=(4.25 + 0.5 * 0.25, 1.3),
        xycoords="data",
        xytext=(4.25 + 0.5 * 0.25, 1.65),
        textcoords="data",
        arrowprops={"arrowstyle": "-|>", "facecolor": "black", "linewidth": 0.5},
        bbox={"pad": 0.0, "linewidth": 0.0, "facecolor": (1.0, 0.0, 0.0, 0.0)},
        ha="center",
    )

    plt.grid()
    plt.gca().set_axisbelow(True)
    plt.gca().xaxis.grid(alpha=0.0)

    plt.xlabel("Age")
    plt.ylabel("Number of persons [x$10^6$]")

    plt.legend()

    plt.tight_layout()
    plt.savefig("%s/age_distribution.pdf" % context.path())
    plt.close()
