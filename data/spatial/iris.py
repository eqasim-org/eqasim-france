import pandas as pd
import geopandas as gpd
import os
import py7zr
import glob

"""
Loads the IRIS zoning system.
"""

def configure(context):
    context.config("data_path")
    context.config("iris_path", "iris_2024")
    context.stage("data.spatial.codes")
    context.config("crs", "EPSG:2154")

def execute(context):
    df_codes = context.stage("data.spatial.codes")

    source_path = find_iris("{}/{}".format(context.config("data_path"), context.config("iris_path")))

    with py7zr.SevenZipFile(source_path) as archive:
        contour_paths = [
            path for path in archive.getnames()
            if "LAMB93" in path or "WGS84" in path
        ]

        archive.extract(context.path(), contour_paths)
    
    gpkg_path = [path for path in contour_paths if path.endswith(".gpkg")]

    if len(gpkg_path) != 1:
        raise RuntimeError("Cannot find IRIS shapes inside the archive, please report this as an error!")

    df_iris = gpd.read_file("{}/{}".format(context.path(), gpkg_path[0]),dtype={"code_iris":str,"code_insee":str})[[
        "code_insee", "code_iris", "geometry"
    ]].rename(columns = {
        "code_iris": "iris_id",
        "code_insee": "commune_id"
    })

    # DEPRECATED: remove with next version of the data sets
    df_iris = fix_2024(df_iris)

    df_iris = df_iris.to_crs(context.config("crs"))

    df_iris["iris_id"] = df_iris["iris_id"].astype("category")
    df_iris["commune_id"] = df_iris["commune_id"].astype("category")

    # Merge with requested codes and verify integrity
    df_iris["iris_id"] = df_iris["iris_id"].astype(df_codes["iris_id"].dtype)
    df_iris["commune_id"] = df_iris["commune_id"].astype(df_codes["commune_id"].dtype)
    df_iris = pd.merge(df_iris, df_codes, on = ["iris_id", "commune_id"])

    requested_iris = set(df_codes["iris_id"].unique())
    merged_iris = set(df_iris["iris_id"].unique())

    if requested_iris != merged_iris:
        raise RuntimeError("Some IRIS are missing: %s" % (requested_iris - merged_iris,))
    
    return df_iris

def find_iris(path):
    candidates = sorted(list(glob.glob("{}/*.7z".format(path))))

    if len(candidates) == 0:
        raise RuntimeError("IRIS data is not available in {}".format(path))
    
    if len(candidates) > 1:
        raise RuntimeError("Multiple candidates for IRIS are available in {}".format(path))
    
    return candidates[0]


def validate(context):
    path = find_iris("{}/{}".format(context.config("data_path"), context.config("iris_path")))
    return os.path.getsize(path)


def fix_2024(df_iris):
    """_summary_
    The 2024 edition of IRIS contains the municipality 14581. Therefore, the data is a bit ahead
    of time since all other data sets that refer to 2024 still contain the this municipality
    with the code 14011. Therefore, we replace the identifier here. This fix can be removed
    for future versions of the data.
    """
    f = df_iris["commune_id"] == "14581"

    # replace municipality
    df_iris.loc[f, "commune_id"] = "14011"

    # replace IRIS
    df_iris.loc[f, "iris_id"] = df_iris.loc[f, "iris_id"].str.replace("14581", "14011")

    return df_iris
