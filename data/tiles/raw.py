import os
import geopandas as gpd
import py7zr
import zipfile
import re
import numpy as np

"""
This stage loads the raw data from the French population income, poverty and living standards in tiled data.
"""

def configure(context):
    context.stage("data.spatial.departments")
    context.config("data_path")
    context.config("tiles_path", "tiles_2019/Filosofi2019_carreaux_200m_gpkg.zip")
    context.config("tiles_file", "carreaux_200m_met.gpkg")


def execute(context):
    # Find relevant departments
    df_departments = context.stage("data.spatial.departments")
    print("Expecting data for {} departments".format(len(df_departments)))
    poly_dep = df_departments.unary_union
    if context.config("tiles_path")[-4:] == ".zip":
        with zipfile.ZipFile(
            "{}/{}".format(context.config("data_path"), context.config("tiles_path"))
        ) as archive:
            with archive.open(
                re.split(r"[/.]", context.config("tiles_path"))[1] + ".7z"
            ) as f:
                with py7zr.SevenZipFile(f) as archive:
                    archive.extract(context.path(), context.config("tiles_file"))
                    df_tiles = gpd.read_file(
                        f'{context.path()}/{context.config("tiles_file")}',
                        mask=poly_dep,
                    )[["idcar_200m", "lcog_geo", "ind", "men", "geometry"]].rename(
                        columns={"idcar_200m": "home_location_id", "men": "weight"}
                    )
    else:
        df_tiles = gpd.read_file(
            f'{context.config("data_path")}/{context.config("tiles_path")}/{context.config("tiles_file")}',
            mask=poly_dep,
        )[["idcar_200m", "lcog_geo", "ind", "men", "geometry"]].rename(
            columns={"idcar_200m": "home_location_id", "men": "weight"}
        )

    df_tiles["home_location_id"] = df_tiles["home_location_id"].str[14:]
    df_tiles["geometry"] = df_tiles["geometry"].centroid
    df_tiles["department_id"] = df_tiles["lcog_geo"].str[:2]

    for department_id in df_departments["departement_id"].values:
        assert np.count_nonzero(df_tiles["department_id"] == department_id) > 0

    return df_tiles[["home_location_id", "weight", "geometry"]]


def validate(context):
    if not os.path.exists(
        "{}/{}".format(context.config("data_path"), context.config("tiles_path"))
    ):
        raise RuntimeError("Tiles 2019 data is not available")

    return os.path.getsize(
        "{}/{}".format(context.config("data_path"), context.config("tiles_path"))
    )