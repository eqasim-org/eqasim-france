import os
import polars as pl

"""
This stage loads the raw data from the French enterprise registry.
"""


def configure(context):
    context.config("data_path")
    context.config("siret_path", "sirene/StockEtablissement_utf8.parquet")

    context.stage("data.spatial.codes")


def execute(context):
    # Filter by departement
    df_codes = context.stage("data.spatial.codes")
    requested_departements = set(df_codes["departement_id"].unique())

    filename = os.path.join(context.config("data_path"), context.config("siret_path"))
    lf = pl.scan_parquet(filename)
    lf = lf.filter(pl.col("codeCommuneEtablissement").is_not_null())
    # The departement code can be read from the 2 first characters of the INSEE commune code, or
    # from the 3 first characters for oversea departements (e.g., Fort-de-France: 97209).
    deps2 = {dep for dep in requested_departements if len(dep) == 2}
    deps3 = {dep for dep in requested_departements if len(dep) == 3}
    assert len(deps2) + len(deps3) == len(requested_departements)
    if deps2:
        lf = lf.filter(pl.col("codeCommuneEtablissement").str.slice(0, 2).is_in(deps2))
    if deps3:
        lf = lf.filter(pl.col("codeCommuneEtablissement").str.slice(0, 3).is_in(deps3))

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
