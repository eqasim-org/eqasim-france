import os
import polars as pl

"""
This stage loads the raw data from the French enterprise registry.
"""


def configure(context):
    context.config("data_path")
    context.config("siren_path", "sirene/StockUniteLegale_utf8.parquet")

    context.stage("data.sirene.raw_siret")


def execute(context):
    relevant_siren = pl.from_pandas(context.stage("data.sirene.raw_siret"))

    filename = os.path.join(context.config("data_path"), context.config("siren_path"))
    df_siren = (
        pl.scan_parquet(filename)
        .join(relevant_siren.lazy(), on="siren", how="semi")
        .select("siren", "categorieJuridiqueUniteLegale")
        .collect()
    )
    return df_siren.to_pandas()


def validate(context):
    filename = os.path.join(context.config("data_path"), context.config("siren_path"))
    if not os.path.isfile(filename):
        raise RuntimeError("SIRENE: SIREN data is not available")
    return os.path.getsize(filename)
