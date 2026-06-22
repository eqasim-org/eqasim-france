import os
import polars as pl

"""
This stage loads the geolocalization data for the French enterprise registry.
"""


def configure(context):
    context.config("data_path")
    context.config(
        "siret_geo_path",
        "sirene/geoloc-geolocalisationetablissement-sirene-pour-etudes-statistiques-parquet.parquet",
    )

    context.stage("data.spatial.codes")


def execute(context):
    # Filter by commune.
    df_codes = context.stage("data.spatial.codes")
    requested_communes = set(df_codes["commune_id"].unique())

    filename = os.path.join(context.config("data_path"), context.config("siret_geo_path"))
    lf = pl.scan_parquet(filename)
    lf = lf.filter(pl.col("plg_code_commune").is_in(requested_communes))
    df_siret_geoloc = lf.select("siret", "x", "y").collect()
    return df_siret_geoloc.to_pandas()


def validate(context):
    filename = os.path.join(context.config("data_path"), context.config("siret_geo_path"))
    if not os.path.isfile(filename):
        raise RuntimeError("SIRENE: geolocaized SIRET data is not available")

    return os.path.getsize(filename)
