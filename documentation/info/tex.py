import numpy as np


def configure(context):
    context.stage("documentation.info.collect")


def execute(context):
    info = context.stage("documentation.info.collect")

    variables = {
        "infoBpeNumberOfEnterprises": "{:,d}".format(
            info["bpe"]["number_of_enterprises"]
        ),
        "infoBpeNumberOfEducationEnterprises": "{:,d}".format(
            info["bpe"]["number_of_education_enterprises"]
        ),
        "infoBpeNumberOfShopEnterprises": "{:,d}".format(
            info["bpe"]["number_of_shop_enterprises"]
        ),
        "infoBpeNumberOfLeisureEnterprises": "{:,d}".format(
            info["bpe"]["number_of_leisure_enterprises"]
        ),
        "infoBpeNumberOfOtherEnterprises": "{:,d}".format(
            info["bpe"]["number_of_other_enterprises"]
        ),
        "infoZonesNumberOfMunicipalities": "{:,d}".format(
            info["zones"]["number_of_municipalities"]
        ),
        "infoZonesNumberOfIris": "{:,d}".format(info["zones"]["number_of_iris"]),
        "infoIncomeMinimumMedian": "{:,.0f}".format(
            1e3 * np.round(info["income"]["minimum_median"] * 1e-3)
        ),
        "infoIncomeMaximumMedian": "{:,.0f}".format(
            1e3 * np.round(info["income"]["maximum_median"] * 1e-3)
        ),
        "infoIncomeMedianRegion": "{:,.0f}".format(
            1e3 * np.round(info["income"]["median_region"] * 1e-3)
        ),
        "infoIncomeNumberOfIncompleteDistributions": "{:,d}".format(
            info["income"]["number_of_incomplete_distributions"]
        ),
        "infoIncomeNumberOfMissingDistributions": "{:,d}".format(
            info["income"]["number_of_missing_distributions"]
        ),
        "infoCensusFilteredHouseholds": "{:.2f}\\%".format(
            1e2 * info["census"]["filtered_households_share"]
        ),
        "infoCensusFilteredPersons": "{:.2f}\\%".format(
            1e2 * info["census"]["filtered_persons_share"]
        ),
    }

    latex = []

    for key, value in variables.items():
        latex.append(r"\newcommand{\%s}{{%s}}" % (key, value))

    with open("%s/info.tex" % context.path(), "w+") as f:
        f.write("\n".join(latex))
