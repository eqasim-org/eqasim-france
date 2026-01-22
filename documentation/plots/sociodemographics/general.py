import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting
import documentation.plots.language as lang
import analysis.marginals

SAMPLING_RATE = 0.05

def configure(context):
    context.config("hts")

    context.stage("analysis.reference.census.sociodemographics")
    context.stage("analysis.reference.hts.sociodemographics")

    context.stage(
        "analysis.synthesis.sociodemographics.general",
        dict(sampling_rate = SAMPLING_RATE), alias = "data"
    )

def get_reference(level, marginal, census, hts):
    if (marginal,) in census[level]:
        return census[level][(marginal,)]
    else:
        return hts[level][(marginal,)]

def prepare_reference(hts_marginals, census_marginals, level, marginal):
    if (marginal,) in census_marginals[level]:
        df = census_marginals[level][(marginal,)]
        df["reference_source"] = "census"
    else:
        df = hts_marginals[level][(marginal,)]
        df["reference_source"] = "hts"

    df = df.copy().rename(columns = { marginal: "value", "weight": "reference" })
    df = df[["value", "reference", "reference_source"]]
    df = df.sort_values(by = "value")

    return df

def prepare_marginal(data_marginals, hts_marginals, census_marginals, level, marginal, sampling_rate):
    df = data_marginals[level][(marginal,)].copy().rename(columns = { marginal: "value" })
    df["attribute"] = marginal
    df = df[["attribute", "value", "mean", "min", "max"]]
    df = df.sort_values(by = "value")

    df["mean"] /= sampling_rate
    df["min"] /= sampling_rate
    df["max"] /= sampling_rate

    df = pd.merge(df, prepare_reference(hts_marginals, census_marginals, level, marginal), on = "value")

    return df

def label(row):
    if row["attribute"] == "age_class":
        return "Age %s" % analysis.marginals.AGE_CLASS_LABELS[row["value"]]

    elif row["attribute"] == "sex":
        return row["value"].capitalize()

    elif row["attribute"] == "employed":
        return "Employed" if row["value"] else "Unemployed"

    elif row["attribute"] == "studies":
        return "Studies %s" % ("Yes" if row["value"] else "No")

    elif row["attribute"] == "has_license":
        return "Driving license %s" % ("Yes" if row["value"] else "No")

    elif row["attribute"] == "has_pt_subscription":
        return "PT Subscription %s" % ("Yes" if row["value"] else "No")

    elif row["attribute"] == "socioprofessional_class":
        return "SC %s" % analysis.marginals.SOCIOPROFESIONAL_CLASS_LABELS[row["value"]]

    elif row["attribute"] == "household_size_class":
        return "Household size %s" % analysis.marginals.HOUSEHOLD_SIZE_LABELS[row["value"]]

    elif row["attribute"] == "number_of_cars_class":
        return "No. vehicles %s" % analysis.marginals.NUMBER_OF_CARS_LABELS[row["value"]]

    elif row["attribute"] == "number_of_bicycles_class":
        return "No. bicycles %s" % analysis.marginals.NUMBER_OF_BICYCLES_LABELS[row["value"]]

def add_labels(df_figure):
    df_figure["label"] = df_figure.apply(label, axis = 1, raw = False)

def prepare_data(data_marginals, hts_marginals, census_marginals, level, marginals, sampling_rate):
    return pd.concat([
        prepare_marginal(data_marginals, hts_marginals, census_marginals, level, marginal, sampling_rate)
        for marginal in marginals
    ])

def reweight_hts(df_figure, hts_marginals, census_marginals, level):
    hts_total = hts_marginals[level][tuple()]["weight"].values[0]
    census_total = census_marginals[level][tuple()]["weight"].values[0]

    f = df_figure["reference_source"] == "hts"
    df_figure.loc[f, "reference"] *= census_total / hts_total

def execute(context):
    plotting.setup()

    hts = context.stage("analysis.reference.hts.sociodemographics")
    census = context.stage("analysis.reference.census.sociodemographics")
    data = context.stage("data")

    figures = [
        dict(
            level = "person", label = "Number of persons", size = (6.0, 5.0),
            marginals = ["age_class", "sex", "employed", "studies", "has_license", "has_pt_subscription", "socioprofessional_class"]
        ),
        dict(
            level = "household", label = "Number of households", size = plotting.WIDE_FIGSIZE,
            marginals = ["household_size_class", "number_of_cars_class", "number_of_bikes_class"]
        )
    ]

    for figure in figures:
        plt.figure(figsize = figure["size"])

        df_figure = prepare_data(data, hts, census, figure["level"], figure["marginals"], SAMPLING_RATE)

        reweight_hts(df_figure, hts, census, figure["level"])
        add_labels(df_figure)

        locations = np.arange(len(df_figure))

        f = (df_figure["reference_source"] == "census").values
        plt.barh(locations[f], df_figure["reference"].values[f], height = 0.4, label = "Census", align = "edge", linewidth = 0.5, edgecolor = "white", color = plotting.COLORS["census"])
        plt.barh(locations[f] + 0.4, df_figure["mean"].values[f], height = 0.4, label = "Synthetic", align = "edge", linewidth = 0.5, edgecolor = "white", color = plotting.COLORS["synthetic"])

        f = (df_figure["reference_source"] == "hts").values
        hts_name = context.config("hts")
        plt.barh(locations[f], df_figure["reference"].values[f], height = 0.4, label = "HTS", align = "edge", linewidth = 0.5, edgecolor = "white", color = plotting.COLORS[hts_name])
        plt.barh(locations[f] + 0.4, df_figure["mean"].values[f], height = 0.4, label = None, align = "edge", linewidth = 0.5, edgecolor = "white", color = plotting.COLORS["synthetic"])

        for index, (min, max) in enumerate(zip(df_figure["min"].values, df_figure["max"].values)):
            location = index + 0.4 + 0.2
            plt.plot([min, max], [location, location], "k", linewidth = 1, label = "Range")

        plt.gca().yaxis.set_major_locator(tck.FixedLocator(locations + 0.4))
        plt.gca().yaxis.set_major_formatter(tck.FixedFormatter(df_figure["label"].values))

        if figure["level"] == "person":
            plt.gca().xaxis.set_major_locator(tck.FixedLocator(np.arange(1, 100) * 1e6 * 2))
            plt.gca().xaxis.set_major_formatter(tck.FuncFormatter(lambda x,p: "%dM" % (x / 1e6,)))

        if figure["level"] == "household":
            plt.gca().xaxis.set_major_locator(tck.FixedLocator(np.arange(1, 100) * 1e6 * 0.5))
            plt.gca().xaxis.set_major_formatter(tck.FuncFormatter(lambda x,p: "%.1fM" % (x / 1e6,)))

        plt.grid()
        plt.gca().set_axisbelow(True)
        plt.gca().yaxis.grid(alpha = 0.0)
        plt.gca().invert_yaxis()

        plt.xlabel(figure["label"])

        handles, labels = plt.gca().get_legend_handles_labels()
        handles = [handles[-2], handles[-1], handles[-3], handles[-4]]
        labels = [labels[-2], labels[-1], labels[-3], labels[-4]]
        plt.legend(handles = handles, labels = labels, loc = "best")

        plt.tight_layout()
        plt.savefig("%s/%s.pdf" % (context.path(), figure["level"]))
        plt.close()
