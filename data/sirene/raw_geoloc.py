import os
import polars as pl

"""
This stage loads the geolocalization data for the French enterprise registry.
"""


def configure(context):
    context.config("data_path")
    context.config(
        "siret_geo_path",
        "sirene/GeolocalisationEtablissement_Sirene_pour_etudes_statistiques_utf8.parquet",
    )

    context.stage("data.spatial.codes")


def execute(context):
    # Filter by departement
    df_codes = context.stage("data.spatial.codes")
    requested_departements = set(df_codes["departement_id"].unique())

    filename = os.path.join(context.config("data_path"), context.config("siret_geo_path"))
    lf = pl.scan_parquet(filename)
    # The departement code can be read from the 2 first characters of the INSEE commune code, or
    # from the 3 first characters for oversea departements (e.g., Fort-de-France: 972).
    deps2 = {dep for dep in requested_departements if len(dep) == 2}
    deps3 = {dep for dep in requested_departements if len(dep) == 3}
    assert len(deps2) + len(deps3) == len(requested_departements)
    if deps2:
        lf = lf.filter(pl.col("plg_code_commune").str.slice(0, 2).is_in(deps2))
    if deps3:
        lf = lf.filter(pl.col("plg_code_commune").str.slice(0, 3).is_in(deps3))
    df_siret_geoloc = lf.select("siret", "x", "y").collect()
    return df_siret_geoloc.to_pandas()


def validate(context):
    filename = os.path.join(context.config("data_path"), context.config("siret_geo_path"))
    if not os.path.isfile(filename):
        raise RuntimeError("SIRENE: geolocaized SIRET data is not available")

    return os.path.getsize(filename)
