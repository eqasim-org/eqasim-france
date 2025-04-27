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
    df_work["commute_mode"] = np.nan
    df_work.loc[df_work["TRANS"] == 1, "commute_mode"] = "no transport"
    df_work.loc[df_work["TRANS"] == 2, "commute_mode"] = "walk"
    df_work.loc[df_work["TRANS"] == 3, "commute_mode"] = "bike"
    df_work.loc[df_work["TRANS"] == 4, "commute_mode"] = "car"
    df_work.loc[df_work["TRANS"] == 5, "commute_mode"] = "car"
    df_work.loc[df_work["TRANS"] == 6, "commute_mode"] = "pt"
    df_work["commute_mode"] = df_work["commute_mode"].astype("category")
    
    assert not np.any(df_work["commute_mode"].isna())

    # Clean age range for education
    df_education["age_range"] = np.nan
    df_education.loc[df_education["AGEREV10"] <= 6, "age_range"] = "primary_school"
    df_education.loc[df_education["AGEREV10"] == 11, "age_range"] = "middle_school"
    df_education.loc[df_education["AGEREV10"] == 15, "age_range"] = "high_school"
    df_education.loc[df_education["AGEREV10"] >= 18, "age_range"] = "higher_education"
    df_education["age_range"] = df_education["age_range"].astype("category")
    
    assert not np.any(df_education["age_range"].isna())

    # Aggregate the flows
    print("Aggregating work ...")
    df_work = df_work.groupby(["origin_id", "destination_id", "commute_mode"])["weight"].sum().reset_index()

    print("Aggregating education ...")
    df_education = df_education.groupby(["origin_id", "destination_id","age_range"])["weight"].sum().reset_index()

    df_work["weight"] = df_work["weight"].fillna(0.0)
    df_education["weight"] = df_education["weight"].fillna(0.0)

    return df_work, df_education
