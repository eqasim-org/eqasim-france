import pandas as pd
import os
import zipfile
import polars as pl
"""
This stage loads the raw data from the French service registry.
"""

def configure(context):
    context.config("data_path")
    context.config("bpe_path", "bpe_2024/BPE24.parquet")
    #context.config("bpe_csv", "BPE24.csv")
    context.stage("data.spatial.codes")

def execute(context):
    df_records = []

    df_codes = context.stage("data.spatial.codes")
    requested_departements = df_codes["departement_id"].unique()

    with context.progress(label = "Reading BPE ...") as progress:
        parquet = pl.read_parquet("{}/{}".format(context.config("data_path"), context.config("bpe_path")), columns = [ "CAPACITE",
                        "DCIRIS", "LAMBERT_X", "LAMBERT_Y",
                        "TYPEQU", "DEPCOM", "DEP"
                    ],
                )

        parquet = parquet.cast( dict(DEPCOM = str, DEP = str, DCIRIS = str))
        parquet = parquet.filter(pl.col("DEP").is_in(requested_departements))

        progress.update(len(parquet))

    return parquet.to_pandas()

def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("bpe_path"))):
        raise RuntimeError("BPE data is not available")

    return os.path.getsize("%s/%s" % (context.config("data_path"), context.config("bpe_path")))
