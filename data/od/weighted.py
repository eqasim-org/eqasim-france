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

def fix_origins(df, commune_ids, purpose,category): 
    df_existing = df.groupby(['origin_id',category])["weight"].sum()
    existing_ids = set(df_existing[df_existing>0].index)
     
    missing_ids = set(product(commune_ids,np.unique(df[category]))) - existing_ids

    rows = []
    for origin_id,category_name in missing_ids:
        for destination_id in commune_ids:
                rows.append((origin_id, destination_id, category_name, 1.0 if origin_id == destination_id else 0.0))

    print("Fixing %d origins for %s" % (len(missing_ids), purpose))

    return pd.concat([df, pd.DataFrame.from_records(
        rows, columns = ["origin_id", "destination_id", category, "weight"]
    )]).sort_values(["origin_id", "destination_id"])

def execute(context):
    df_codes = context.stage("data.spatial.codes")
    commune_ids = set(df_codes["commune_id"].unique())

    # Load data
    df_work, df_education = context.stage("data.od.cleaned")

    # Add missing origins
    df_work = fix_origins(df_work, commune_ids, "work","commute_mode")
    df_education = fix_origins(df_education, commune_ids, "education","age_range")

    # Aggregate work (we do not consider different modes at the moment)
    df_work = df_work[["origin_id", "destination_id", "weight"]].groupby(["origin_id", "destination_id"]).sum().reset_index()
   
    # Compute totals
    df_total = df_work[["origin_id", "weight"]].groupby("origin_id",observed=False).sum().reset_index().rename({ "weight" : "total" }, axis = 1)
    df_work = pd.merge(df_work, df_total, on = "origin_id")

    df_total = df_education[["origin_id","age_range", "weight"]].groupby(["origin_id","age_range"],observed=False).sum().reset_index().rename({ "weight" : "total" }, axis = 1)
    df_education = pd.merge(df_education, df_total, on = ["origin_id","age_range"])
    
    if context.config("education_location_source") == 'bpe':
        # Aggregate education (we do not consider different age range with bpe source)
        df_education = df_education[["origin_id", "destination_id", "weight","total"]].groupby(["origin_id", "destination_id"],observed=False).sum().reset_index()    
    # Compute weight
    df_work["weight"] /= df_work["total"]
    df_education["weight"] /= df_education["total"]

    del df_work["total"]
    del df_education["total"]
    
    return df_work, df_education
