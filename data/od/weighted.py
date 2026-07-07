from tqdm import tqdm
import pandas as pd
import numpy as np
from itertools import product

"""
Transforms absolute OD flows from French census into a weighted destination
matrix given a certain origin commune for work and education.

Potential TODO: Do this by mode of transport!
"""

def configure(context):
    context.stage("data.od.cleaned")
    context.stage("data.spatial.codes")

    context.config("education_location_source","bpe")

def fix_origins(df, commune_ids, purpose, category):
    df_existing = df.groupby(["origin_id", category])["weight"].sum()
    
    # find missing origin x category combinations
    existing = set(df_existing[df_existing > 0.0].index)
    missing = np.array(list(set(product(
        commune_ids, df[category].cat.categories.values)) - existing))
    
    # for each missing origin x category we create a flow to itself
    df_missing = pd.DataFrame({
        "origin_id": pd.Categorical(missing[:, 0], dtype = df["origin_id"].dtype),
        "destination_id": pd.Categorical(missing[:, 0], dtype = df["destination_id"].dtype),
        category: pd.Categorical(missing[:, 1], dtype = df[category].dtype),
        "weight": 1.0
    }).sort_values(by = ["origin_id", "destination_id", category])

    print("Fixed {} origins for {}".format(len(df_missing), purpose))
    return pd.concat([df, df_missing])

def execute(context):
    df_codes = context.stage("data.spatial.codes")
    commune_ids = set(df_codes["commune_id"].unique())

    print("len codes", len(df_codes))
    print("len communes", len(commune_ids))

    # Load data
    df_work, df_education = context.stage("data.od.cleaned")

    print("len df_work", len(df_work))
    print("len df_education", len(df_education))

    # Add missing origins
    df_work = fix_origins(df_work, commune_ids, "work", "commute_mode")
    df_education = fix_origins(df_education, commune_ids, "education", "age_range")

    print("len df_work after fix", len(df_work))
    print("len df_education after fix", len(df_education))

    # Aggregate work (we do not consider different modes at the moment)
    df_work = df_work[["origin_id", "destination_id", "weight"]].groupby(["origin_id", "destination_id"]).sum().reset_index()
   
    # Compute totals
    df_total = df_work[["origin_id", "weight"]].groupby("origin_id").sum().reset_index().rename({ "weight" : "total" }, axis = 1)
    df_work = pd.merge(df_work, df_total, on = "origin_id")

    print("len df_work after aggregation", len(df_work))

    df_total = df_education[["origin_id","age_range", "weight"]].groupby(["origin_id","age_range"]).sum().reset_index().rename({ "weight" : "total" }, axis = 1)
    df_education = pd.merge(df_education, df_total, on = ["origin_id","age_range"])
    
    print("len df_education after first aggregation", len(df_education))

    if context.config("education_location_source") == 'bpe':
        # Aggregate education (we do not consider different age range with bpe source)
        df_education = df_education[["origin_id", "destination_id", "weight", "total"]].groupby(["origin_id", "destination_id"]).sum().reset_index()    
    
    print("len df_education after second aggregation", len(df_education))

    # Compute weight
    df_work["weight"] /= df_work["total"]
    df_education["weight"] /= df_education["total"]

    del df_work["total"]
    del df_education["total"]

    assert not np.any(df_work["weight"].isna())
    assert not np.any(df_education["weight"].isna())

    # at this point, we have a SPARSE flow matrix with the following properties:
    # each origin x category combination exists at least one with a flow to itself
    # each origin x category combination, however, may have multiple destinations
    
    return df_work, df_education
