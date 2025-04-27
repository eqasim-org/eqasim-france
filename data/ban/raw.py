import os, glob
import pandas as pd
import geopandas as gpd
import numpy as np

"""
This stage loads the raw data from the new French address registry (BAN).
"""

def configure(context):
    context.stage("data.spatial.codes")

    context.config("data_path")
    context.config("ban_path", "ban_idf")

BAN_DTYPES = {
    "code_insee": str,
    "x": float, 
    "y": float
}

def execute(context):
    # Find relevant departments
    df_codes = context.stage("data.spatial.codes")
    requested_departments = set(df_codes["departement_id"].unique())

    # Load BAN
    df_ban = []

    for source_path in find_ban("{}/{}".format(context.config("data_path"), context.config("ban_path"))):
        print("Reading {} ...".format(source_path))

        df_partial = pd.read_csv(source_path, 
            compression = "gzip", sep = ";", usecols = BAN_DTYPES.keys(), dtype = BAN_DTYPES)
        
        # Filter by departments
        df_partial["department_id"] = df_partial["code_insee"].str[:2]
        df_partial = df_partial[["department_id", "x", "y"]]
        df_partial = df_partial[df_partial["department_id"].isin(requested_departments)]

        if len(df_partial) > 0:
            df_ban.append(df_partial)
    
    df_ban = pd.concat(df_ban)
    df_ban = gpd.GeoDataFrame(
        df_ban, geometry = gpd.points_from_xy(df_ban.x, df_ban.y), crs = "EPSG:2154")
    
    # Check that we cover all requested departments at least once
    for department_id in requested_departments:
        assert np.count_nonzero(df_ban["department_id"] == department_id) > 0

    return df_ban[["geometry"]]

def find_ban(path):
    candidates = sorted(list(glob.glob("{}/*.csv.gz".format(path))))

    if len(candidates) == 0:
        raise RuntimeError("BAN data is not available in {}".format(path))
    
    return candidates

def validate(context):
    paths = find_ban("{}/{}".format(context.config("data_path"), context.config("ban_path")))
    return sum([os.path.getsize(path) for path in paths])
