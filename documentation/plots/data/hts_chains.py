import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting


def configure(context):
    context.stage("analysis.reference.hts.chains", {"hts": "egt"}, alias="egt")
    context.stage("analysis.reference.hts.chains", {"hts": "entd"}, alias="entd")


def execute(context):
    plotting.setup()

    marginal = ("age_range", "sex", "chain")
    df_egt = context.stage("egt")[marginal].rename(columns={"weight": "egt"})
    df_entd = context.stage("entd")[marginal].rename(columns={"weight": "entd"})

    df = pd.merge(df_egt, df_entd, on=["age_range", "sex", "chain"])
    df = df[df["age_range"]]

    df_female = (
        df[df["sex"] == "female"].sort_values(by="egt", ascending=False).head(10)
    )
    df_male = df[df["sex"] == "male"].sort_values(by="egt", ascending=False).head(10)

    plt.figure(figsize=plotting.WIDE_FIGSIZE)

    for index, (df, title) in enumerate(
        zip([df_male, df_female], ["Male (18-40)", "Female (18-40)"])
    ):
        plt.subplot(1, 2, index + 1)

        plt.bar(
            np.arange(10),
            df["egt"],
            width=0.4,
            label="EGT",
            align="edge",
            linewidth=0.5,
            edgecolor="white",
            color=plotting.COLORS["egt"],
        )
        plt.bar(
            np.arange(10) + 0.4,
            df["entd"],
            width=0.4,
            label="ENTD",
            align="edge",
            linewidth=0.5,
            edgecolor="white",
            color=plotting.COLORS["entd"],
        )

        plt.grid()
        plt.gca().set_axisbelow(True)
        plt.gca().xaxis.grid(alpha=0.0)

        plt.gca().yaxis.set_major_locator(tck.FixedLocator(np.arange(100) * 1e5))
        plt.gca().yaxis.set_major_formatter(
            tck.FuncFormatter(lambda x, p: "%d" % (x * 1e-3,))
        )

        plt.gca().xaxis.set_major_locator(tck.FixedLocator(np.arange(10) + 0.4))
        plt.gca().xaxis.set_major_formatter(
            tck.FuncFormatter(lambda x, p: "\n".join(df["chain"].values[p]).upper())
        )

        if index == 1:
            plt.gca().yaxis.set_major_formatter(tck.FixedFormatter([""] * 1000))
            plt.gca().yaxis.get_label().set_visible(False)

        plt.legend(loc="best", title=title)

        if index == 0:
            plt.ylabel("Number of persons [x1000]")

    plt.tight_layout()
    plt.show()
    plt.savefig("%s/activity_chains.pdf" % context.path())
    plt.close()
