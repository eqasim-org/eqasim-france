import pandas as pd
import geopandas as gpd
import os

"""
This stage loads the raw data of the specified HTS (EMC2 Gironde).

Adapted from the first implementation by Valentin Le Besond (IFSTTAR Nantes)
and second implementation by Sebastian Hoërl
"""

def configure(context):
    context.config("data_path")
    
def execute(context):
    # Load households
    df_spatial = gpd.read_file(
        "%s/emc2_33_2021/spatial/EMC2_Gironde_2022_ZF_160.shp"
        % context.config("data_path"))

    df_spatial = df_spatial[["NUM_COM","ZF_160","geometry"]].copy()
    df_spatial = df_spatial.rename(columns={"NUM_COM":"commune_id","ZF_160":"zone_id"})
    df_spatial["commune_id"] = df_spatial["commune_id"].astype(str)

    return df_spatial

FILES = [
    "spatial/EMC2_Gironde_2022_ZF_160.shp"
]

def validate(context):
    for name in FILES:
        if not os.path.exists("%s/emc2_33_2021/%s" % (context.config("data_path"), name)):
            raise RuntimeError("File missing from EMC2: %s" % name)

    return [
        os.path.getsize("%s/emc2_33_2021/%s" % (context.config("data_path"), name))
        for name in FILES
    ]
