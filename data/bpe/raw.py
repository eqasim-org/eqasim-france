import polars as pl
import os
import zipfile

"""
This stage loads the raw data from the French service registry.
"""

def configure(context):
    context.config("data_path")
    context.config("bpe_path", "bpe_2021/bpe21_ensemble_xy_csv.zip")
    context.config("bpe_csv", "bpe21_ensemble_xy.csv")
    context.stage("data.spatial.codes")

def execute(context):
    df_codes = context.stage("data.spatial.codes")
    requested_departements = list(map(str, df_codes["departement_id"].unique()))

    with zipfile.ZipFile(
        os.path.join(context.config("data_path"), context.config("bpe_path"))
    ) as archive:
        with archive.open(context.config("bpe_csv")) as f:
            df = pl.read_csv(
                f.read(),
                separator=";",
                columns=["DCIRIS", "LAMBERT_X", "LAMBERT_Y", "TYPEQU", "DEPCOM", "DEP"],
                schema_overrides={"DEPCOM": pl.String, "DEP": pl.String, "DCIRIS": pl.String},
            )

    df = df.filter(pl.col("DEP").is_in(requested_departements))

    return df.to_pandas()

def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("bpe_path"))):
        raise RuntimeError("BPE data is not available")

    return os.path.getsize("%s/%s" % (context.config("data_path"), context.config("bpe_path")))
