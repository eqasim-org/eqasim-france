import pandas as pd
import geopandas as gpd
import os
import numpy as np

"""
This stage loads the raw data of the specified HTS (EMC2 Gironde).

Adapted from the first implementation by Valentin Le Besond (IFSTTAR Nantes)
and second implementation by Sebastian Hoërl
"""

def configure(context):
    context.stage("data.hts.emc2_33.spatial")
    context.stage("data.spatial.urban_type")
    
       
def execute(context):
    df_spatial = context.stage("data.hts.emc2_33.spatial")
    df_urban_types = context.stage("data.spatial.urban_type")
    
    df_spatial = df_spatial.merge(df_urban_types,on="commune_id",how="left")
    df_spatial.loc[df_spatial["urban_type"].isna(),"urban_type"] = "none"
    print(df_spatial.loc[df_spatial["urban_type"].isna()])
    df_spatial["urban_type"] = df_spatial["urban_type"].astype("category")
    
    return df_spatial
