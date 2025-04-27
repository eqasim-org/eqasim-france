import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as tck

import documentation.plotting as plotting

SAMPLING_RATE = 0.05

def configure(context):
    context.stage("data.income.municipality")

    context.stage("analysis.synthesis.income", dict(sampling_rate = SAMPLING_RATE), alias = "data")
    context.stage("analysis.reference.income")

def execute(context):
    plotting.setup()

    # Income imputation
    df_income = context.stage("data.income.municipality")
    df_income = df_income[(df_income["attribute"] == "all") & (df_income["value"] == "all")]
    df_imputed = df_income[df_income["is_imputed"]]

    plt.figure()

    minimum = min(df_imputed["reference_median"].min(), df_imputed["q5"].min()) * 1e-3
    maximum = max(df_imputed["reference_median"].max(), df_imputed["q5"].max()) * 1e-3
    plt.plot([minimum, maximum], [minimum, maximum], "k--")

    f = ~df_imputed["is_missing"]
    plt.plot(df_imputed[f]["reference_median"] * 1e-3, df_imputed[f]["q5"] * 1e-3, '.', markersize = 3, color = plotting.COLORSET[0], label = "y")
    plt.plot(df_imputed[~f]["reference_median"] * 1e-3, df_imputed[~f]["q5"] * 1e-3, 'x', markersize = 3, color = plotting.COLORSET[1])

    plt.xlabel("Reference median income [1000 EUR]")
    plt.ylabel("Imputed median income [1000 EUR]")
    plt.grid()

    plt.tight_layout()
    plt.savefig("%s/income_imputation.pdf" % context.path())
    plt.close()

    # Income distributions
    plt.figure()

    df_data = context.stage("data")
    df_reference = context.stage("analysis.reference.income")

    f = df_reference["source"] == "entd"
    plt.plot(df_reference[f]["income"].values * 1e-3, df_reference[f]["cdf"].values, color = plotting.COLORS["entd"], label = "ENTD", linewidth = 1.0)

    f = df_reference["source"] == "egt"
    plt.plot(df_reference[f]["income"].values * 1e-3, df_reference[f]["cdf"].values, color = plotting.COLORS["egt"], label = "EGT", linewidth = 1.0)

    f = df_reference["source"] == "filo"
    plt.plot(df_reference[f]["income"].values * 1e-3, df_reference[f]["cdf"].values, color = plotting.COLORS["census"], label = "Tax data", linewidth = 1.0, marker = ".", markersize = 3)

    plt.plot(df_data["mean"].values * 1e-3, df_data["cdf"].values, color = "k", label = "Synthetic", linewidth = 1.0, linestyle = ":")
    plt.fill_betweenx(df_data["cdf"].values, df_data["min"].values * 1e-3, df_data["max"].values * 1e-3, color = "k", linewidth = 0.0, alpha = 0.25)

    plt.xlim([0, 60])

    plt.xlabel("Household income [1000 EUR]")
    plt.ylabel("Cumulative density")

    plt.legend(loc = "lower right")
    plt.grid()

    plt.tight_layout()
    plt.savefig("%s/income_distributions.pdf" % context.path())
    plt.close()
