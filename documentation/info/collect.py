import numpy as np
import json

def configure(context):
    context.stage("data.hts.comparison")
    context.stage("data.census.cleaned")
    context.stage("data.od.cleaned")
    context.stage("data.bpe.cleaned")
    context.stage("data.spatial.codes")
    context.stage("data.income.municipality")
    context.stage("data.income.region")
    context.stage("data.census.filtered")
    context.stage("data.sirene.localized")

def execute(context):
    info = {}

    # Get HTS Comparison data
    hts_comparison = context.stage("data.hts.comparison")
    info["hts"] = hts_comparison["info"]

    # Get census data
    df_census = context.stage("data.census.cleaned")
    df_households = df_census.drop_duplicates("household_id")

    info["census"] = {
        "number_of_households": len(df_census["household_id"].unique()),
        "number_of_persons": len(df_census),
        "weighted_number_of_households": df_census[["household_id", "weight"]].drop_duplicates("household_id")["weight"].sum(),
        "weighted_number_of_persons": df_census["weight"].sum(),
        "share_of_households_without_iris": np.sum(df_households[~(df_households["iris_id"] != "undefined") & (df_households["commune_id"] != "undefined")]["weight"]) / np.sum(df_households["weight"]),
        "share_of_households_without_commune": np.sum(df_households[~(df_households["iris_id"] != "undefined") & ~(df_households["commune_id"] != "undefined")]["weight"]) / np.sum(df_households["weight"]),
        "filtered_households_share": context.get_info("data.census.filtered", "filtered_households_share"),
        "filtered_persons_share": context.get_info("data.census.filtered", "filtered_persons_share"),
    }

    # OD data
    df_od_work, df_od_education = context.stage("data.od.cleaned")

    info["od"] = {
        "number_of_work_commutes": len(df_od_work),
        "number_of_education_commutes": len(df_od_education)
    }

    # BPE
    df_bpe = context.stage("data.bpe.cleaned")

    info["bpe"] = {
        "number_of_enterprises": len(df_bpe),
        "number_of_shop_enterprises": int(np.sum(df_bpe["activity_type"] == "shop")),
        "number_of_leisure_enterprises": int(np.sum(df_bpe["activity_type"] == "leisure")),
        "number_of_education_enterprises": int(np.sum(df_bpe["activity_type"] == "education")),
        "number_of_other_enterprises": int(np.sum(df_bpe["activity_type"] == "other")),
    }

    # Zones
    df_codes = context.stage("data.spatial.codes")

    info["zones"] = {
        "number_of_municipalities": len(df_codes["commune_id"].unique()),
        "number_of_iris": len(df_codes["iris_id"].unique())
    }

    with open("%s/zones.json" % context.cache_path, "w+") as f:
        json.dump(info, f, indent = True)

    # Income
    df_income_municipality = context.stage("data.income.municipality")
    df_income_municipality = df_income_municipality[(df_income_municipality["attribute"] == "all") & (df_income_municipality["value"] == "all")]
    df_income_region = context.stage("data.income.region")

    info["income"] = {
        "minimum_median": int(df_income_municipality["q5"].min()),
        "maximum_median": int(df_income_municipality["q5"].max()),
        "median_region": int(df_income_region[4]),
        "number_of_incomplete_distributions": int(np.sum(~df_income_municipality["is_missing"] & df_income_municipality["is_imputed"])),
        "number_of_missing_distributions": int(np.sum(df_income_municipality["is_missing"]))
    }


    # Output
    with open("%s/info.json" % context.cache_path, "w+") as f:
        json.dump(info, f, indent = True)

    return info
