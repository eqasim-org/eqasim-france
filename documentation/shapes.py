import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import palettable

def configure(context):
    context.stage("data.income.municipality")
    context.stage("data.spatial.municipalities")
    context.stage("data.bpe.cleaned")

def execute(context):
    df_communes = context.stage("data.spatial.municipalities")

    # Spatial income distribution
    df_income = context.stage("data.income.municipality")
    df_income = df_income[(df_income["attribute"] == "all") & (df_income["value"] == "all")]
    df_income = pd.merge(df_communes, df_income, how = "inner", on = "commune_id")
    df_income["is_imputed"] = df_income["is_imputed"].astype(int)
    df_income["commune_id"] = df_income["commune_id"].astype(str)
    df_income["departement_id"] = df_income["departement_id"].astype(str)
    df_income.to_file("%s/income.geojson" % context.cache_path, driver = "GeoJSON")

    # Enterprises
    df_bpe = context.stage("data.bpe.cleaned")[["enterprise_id", "geometry", "imputed", "commune_id"]].copy()
    df_bpe["imputed"] = df_bpe["imputed"].astype(int)
    df_bpe["commune_id"] = df_bpe["commune_id"].astype(str)
    df_bpe = df_bpe.iloc[np.random.choice(len(df_bpe), size = 10000, replace = False)]
    df_bpe.to_file("%s/bpe.shp" % context.cache_path)

    return context.cache_path
