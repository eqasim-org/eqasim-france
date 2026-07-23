import os, glob
import pandas as pd
import geopandas as gpd

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
    # Find relevant communes.
    df_codes = context.stage("data.spatial.codes")
    requested_communes = set(df_codes["commune_id"].unique())

    # Load BAN
    df_ban = []

    for source_path in find_ban("{}/{}".format(context.config("data_path"), context.config("ban_path"))):
        print("Reading {} ...".format(source_path))

        df_partial = pd.read_csv(source_path,
            compression = "gzip", sep = ";", usecols = BAN_DTYPES.keys(), dtype = BAN_DTYPES)
        
        # Filter by commune.
        df_partial["commune_id"] = df_partial["code_insee"].str[:5]
        df_partial = df_partial[["commune_id", "x", "y"]]
        df_partial = df_partial[df_partial["commune_id"].isin(requested_communes)]

        if len(df_partial) > 0:
            df_ban.append(df_partial)
    
    if len(df_ban) > 0:
        df_ban = pd.concat(df_ban, ignore_index = True)
    else:
        df_ban = pd.DataFrame(columns = ["commune_id", "x", "y"])

    df_ban = gpd.GeoDataFrame(
        df_ban, geometry = gpd.points_from_xy(df_ban.x, df_ban.y), crs = "EPSG:2154")
    
    # Check that we cover all requested communes at least once.
    # Report the corresponding IRIS and department to make missing BAN
    # coverage easier to diagnose than a bare AssertionError.
    available_communes = set(df_ban["commune_id"].astype(str).unique())
    requested_communes = set(map(str, requested_communes))
    missing_communes = requested_communes - available_communes

    if missing_communes:
        missing_codes = df_codes[
            df_codes["commune_id"].astype(str).isin(missing_communes)
        ][["iris_id", "commune_id", "departement_id"]].drop_duplicates()

        print("Warning: communes missing in BAN; continuing with available addresses:")
        print(missing_codes.sort_values("commune_id").to_string(index=False))


    return df_ban[["geometry"]]

def find_ban(path):
    candidates = sorted(list(glob.glob("{}/*.csv.gz".format(path))))

    if len(candidates) == 0:
        raise RuntimeError("BAN data is not available in {}".format(path))
    
    return candidates

def validate(context):
    paths = find_ban("{}/{}".format(context.config("data_path"), context.config("ban_path")))
    return sum([os.path.getsize(path) for path in paths])
