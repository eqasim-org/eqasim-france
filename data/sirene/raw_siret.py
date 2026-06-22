import os
import polars as pl

"""
This stage loads the raw data from the French enterprise registry.
"""


def configure(context):
    context.config("data_path")
    context.config("siret_path", "sirene/stock-stocketablissement-parquet.parquet")

    context.stage("data.spatial.codes")


def execute(context):
    # Filter by commune.
    df_codes = context.stage("data.spatial.codes")
    requested_communes = set(df_codes["commune_id"].unique())

    filename = os.path.join(context.config("data_path"), context.config("siret_path"))
    lf = pl.scan_parquet(filename)
    lf = lf.filter(pl.col("codeCommuneEtablissement").is_not_null())
    lf = lf.filter(pl.col("codeCommuneEtablissement").is_in(requested_communes))

    df_siret = lf.select(
        "siren",
        "siret",
        "codeCommuneEtablissement",
        "activitePrincipaleEtablissement",
        "trancheEffectifsEtablissement",
        "etatAdministratifEtablissement",
    ).collect()

    return df_siret.to_pandas()


def validate(context):
    filename = os.path.join(context.config("data_path"), context.config("siret_path"))
    if not os.path.isfile(filename):
        raise RuntimeError("SIRENE: SIRET data is not available")
    return os.path.getsize(filename)
