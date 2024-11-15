import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting

SAMPLING_RATE = 0.05


def configure(context):
    context.config("hts")

    context.stage("analysis.reference.od.commute_flow", alias="census")
    context.stage("analysis.reference.hts.commute_flow", alias="hts")
    context.stage(
        "analysis.synthesis.commute_flow",
        dict(sampling_rate=SAMPLING_RATE),
        alias="data",
    )


def execute(context):
    plotting.setup()
    hts_name = context.config("hts")

    df_census = context.stage("census")
    df_hts, df_correction = context.stage("hts")

    # PLOT: Work / education flows
    plt.figure(figsize=plotting.WIDE_FIGSIZE)

    figures = [
        {"slot": "work", "title": "Work", "top": 12},
        {"slot": "education", "title": "Education", "top": 12, "factor": 0.7},
    ]

    for index, figure in enumerate(figures):
        plt.subplot(1, 2, index + 1)
        slot = figure["slot"]

        df = context.stage("data")[slot]
        df = pd.merge(
            df,
            df_census[slot].rename(columns={"weight": "reference"}),
            on=["home", slot],
        )
        df = pd.merge(df, df_correction[slot], on="home")
        df["scaled_reference"] = df["reference"] * (
            figure["factor"] if "factor" in figure else df["factor"]
        )

        count = figure["top"]
        df = df.sort_values(by="scaled_reference", ascending=False).head(count)

        plt.bar(
            np.arange(count),
            df["reference"],
            width=0.4,
            align="edge",
            linewidth=0.5,
            edgecolor="white",
            color=plotting.COLORS["census"],
            alpha=0.25,
        )
        plt.bar(
            np.arange(count),
            df["scaled_reference"],
            width=0.4,
            label="Census",
            align="edge",
            linewidth=0.5,
            edgecolor="white",
            color=plotting.COLORS["census"],
        )
        plt.bar(
            np.arange(count) + 0.4,
            df["mean"] / SAMPLING_RATE,
            width=0.4,
            label="Synthetic",
            align="edge",
            linewidth=0.5,
            edgecolor="white",
            color=plotting.COLORS["synthetic"],
        )

        for index, (min, max) in enumerate(zip(df["min"].values, df["max"].values)):
            index += 0.4 + 0.2
            plt.plot(
                [index, index],
                [min / SAMPLING_RATE, max / SAMPLING_RATE],
                color="k",
                linewidth=1.0,
            )

        plt.grid()
        plt.gca().set_axisbelow(True)
        plt.gca().xaxis.grid(alpha=0.0)

        plt.gca().yaxis.set_major_locator(tck.FixedLocator(np.arange(100) * 1e5))
        plt.gca().yaxis.set_major_formatter(
            tck.FuncFormatter(lambda x, p: "%d" % (x * 1e-3,))
        )

        origins, destinations = df["home"].values, df[figure["slot"]].values

        plt.gca().xaxis.set_major_locator(tck.FixedLocator(np.arange(count) + 0.4))
        plt.gca().xaxis.set_major_formatter(
            tck.FixedFormatter(["%s\n%s" % item for item in zip(origins, destinations)])
        )

        plt.ylabel("Commuters [x1000]")
        plt.legend(loc="best")
        plt.title(figure["title"])

    plt.tight_layout()
    plt.savefig("%s/commute_flows.pdf" % context.path())
    plt.close()

    # PLOT: Scatter
    plt.figure(figsize=plotting.SHORT_FIGSIZE)

    parts = [
        {"slot": "work", "title": "Work", "marker": ".", "color": "k"},
        {
            "slot": "education",
            "title": "Education",
            "factor": 0.7,
            "marker": ".",
            "color": plotting.COLORS[hts_name],
        },
    ]

    minimum = np.inf
    maximum = -np.inf

    for part in parts:
        slot = part["slot"]

        df = context.stage("data")[slot]
        df = pd.merge(
            df,
            df_census[slot].rename(columns={"weight": "reference"}),
            on=["home", slot],
        )
        df = pd.merge(df, df_correction[slot], on="home")
        df["scaled_reference"] = df["reference"] * (
            part["factor"] if "factor" in part else df["factor"]
        )

        plt.loglog(
            df["scaled_reference"],
            df["mean"] / SAMPLING_RATE,
            markersize=2,
            marker=part["marker"],
            color=part["color"],
            linestyle="none",
            label=part["title"],
        )

        minimum = np.minimum(minimum, df["scaled_reference"].min() * 0.9)
        maximum = np.maximum(maximum, df["scaled_reference"].max() * 1.1)

    x = np.linspace(minimum, maximum, 100)
    plt.fill_between(
        x, x * 0.8, x * 1.2, color="k", alpha=0.2, linewidth=0.0, label=r"20% Error"
    )

    plt.xlim([minimum, maximum])
    plt.ylim([minimum, maximum])

    plt.grid()
    plt.gca().set_axisbelow(True)
    plt.legend()

    plt.xlabel("Reference flow")
    plt.ylabel("Synthetic flow")

    plt.tight_layout()
    plt.savefig("%s/commute_scatter.pdf" % context.path())
    plt.close()

    # PLOT: Histogram
    plt.figure(figsize=plotting.SHORT_FIGSIZE)

    parts = [
        {"slot": "work", "title": "Work"},
        {"slot": "education", "title": "Education", "factor": 0.7},
    ]

    for index, part in enumerate(parts):
        slot = part["slot"]

        df = context.stage("data")[slot]
        df = pd.merge(
            df,
            df_census[slot].rename(columns={"weight": "reference"}),
            on=["home", slot],
        )
        df = pd.merge(df, df_correction[slot], on="home")
        df["scaled_reference"] = df["reference"] * (
            part["factor"] if "factor" in part else df["factor"]
        )

        df["difference"] = (
            100
            * (df["mean"] / SAMPLING_RATE - df["scaled_reference"])
            / df["scaled_reference"]
        )

        min = df["difference"].min()
        max = df["difference"].max()
        mean = df["difference"].mean()

        values = df["difference"].values
        outliers = values  # values[(values < min) | (values > max)]

        plt.plot([index - 0.2, index + 0.2], [min, min], color="k", linewidth=1.0)
        plt.plot([index - 0.2, index + 0.2], [max, max], color="k", linewidth=1.0)
        plt.plot(
            [index - 0.2, index + 0.2],
            [mean, mean],
            color="k",
            linewidth=1.0,
            linestyle=":",
        )
        plt.plot([index - 0.2, index - 0.2], [min, max], color="k", linewidth=1.0)
        plt.plot([index + 0.2, index + 0.2], [min, max], color="k", linewidth=1.0)

        plt.plot(
            [index] * len(outliers),
            outliers,
            color="k",
            marker=".",
            markersize=2,
            linestyle="none",
        )

    plt.gca().xaxis.set_major_locator(tck.FixedLocator([0, 1]))
    plt.gca().xaxis.set_major_formatter(tck.FixedFormatter(["Work", "Education"]))

    plt.ylabel("Error [%]")

    plt.xlim([-0.5, 1.5])
    plt.grid()
    plt.gca().set_axisbelow(True)
    plt.gca().xaxis.grid(alpha=0.0)

    plt.bar(
        [np.nan], [np.nan], color="none", edgecolor="k", linewidth=1.0, label="5% - 95%"
    )
    plt.plot([np.nan], color="k", linestyle=":", label="Mean")

    plt.legend(loc="best")

    plt.tight_layout()
    plt.savefig("%s/commute_flow_boxplot.pdf" % context.path())
    plt.close()
