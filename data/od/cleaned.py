import pandas as pd
import numpy as np

"""
Cleans OD data to arrive at OD flows between municipalities for work
and education.
"""

def configure(context):
    context.stage("data.od.raw")
    context.stage("data.spatial.codes")

RENAME = { "COMMUNE" : "origin_id", "DCLT" : "destination_id", "IPONDI" : "weight", "DCETUF" : "destination_id" }

def execute(context):
    
    
    # Load data
    df_work, df_education = context.stage("data.od.raw")

    # Renaming
    df_work = df_work.rename(RENAME, axis = 1)
    df_education = df_education.rename(RENAME, axis = 1)

    # Fix arrondissements
    df_work.loc[~df_work["ARM"].str.contains("Z"), "origin_id"] = df_work["ARM"]
    df_education.loc[~df_education["ARM"].str.contains("Z"), "origin_id"] = df_education["ARM"]

    # Verify spatial data for work
    df_codes = context.stage("data.spatial.codes")

    df_work["origin_id"] = df_work["origin_id"].astype("category")
    df_work["destination_id"] = df_work["destination_id"].astype("category")

    excess_communes = (set(df_work["origin_id"].unique()) | set(df_work["destination_id"].unique())) - set(df_codes["commune_id"].unique())
    if len(excess_communes) > 0:
        raise RuntimeError("Found additional communes: %s" % excess_communes)

    # Verify spatial data for education
    df_codes = context.stage("data.spatial.codes")

    df_education["origin_id"] = df_education["origin_id"].astype("category")
    df_education["destination_id"] = df_education["destination_id"].astype("category")

    excess_communes = (set(df_education["origin_id"].unique()) | set(df_education["destination_id"].unique())) - set(df_codes["commune_id"].unique())
    if len(excess_communes) > 0:
        raise RuntimeError("Found additional communes: %s" % excess_communes)

    # Clean commute mode for work
    categories = ["no transport", "walk", "bike", "car", "pt"]

    df_work["commute_mode"] = pd.Categorical.from_codes(df_work["TRANS"].map({
        1: categories.index("no transport"),
        2: categories.index("walk"),
        3: categories.index("bike"),
        4: categories.index("car"), 
        5: categories.index("car"),
        6: categories.index("pt"),
    }), categories)

    # Clean age range for education
    categories = ["primary_school", "middle_school", "high_school", "higher_education"]

    df_education["AGEREV10"] = df_education["AGEREV10"].astype(int)
    df_education["age_code"] = 0

    df_education.loc[df_education["AGEREV10"] <= 6, "age_code"] = 0
    df_education.loc[df_education["AGEREV10"] == 11, "age_code"] = 1
    df_education.loc[df_education["AGEREV10"] == 15, "age_code"] = 2
    df_education.loc[df_education["AGEREV10"] >= 18, "age_code"] = 3

    df_education["age_range"] = pd.Categorical.from_codes(
        df_education["age_code"], categories)

    # Aggregate the flows
    print("Aggregating work ...")
    df_work = df_work.groupby(["origin_id", "destination_id", "commute_mode"],observed=False)["weight"].sum().reset_index()

    print("Aggregating education ...")
    df_education = df_education.groupby(["origin_id", "destination_id","age_range"],observed=False)["weight"].sum().reset_index()

    df_work["weight"] = df_work["weight"].fillna(0.0)
    df_education["weight"] = df_education["weight"].fillna(0.0)

    return df_work, df_education
