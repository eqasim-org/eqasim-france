import pandas as pd
import polars as pl
import os
import zipfile

"""
Loads raw OD data from French census data.
"""

def configure(context):
    context.stage("data.spatial.codes")
    context.config("data_path")
    context.config("od_pro_path", "rp_2019/RP2019_MOBPRO_csv.zip")
    context.config("od_sco_path", "rp_2019/RP2019_MOBSCO_csv.zip")
    context.config("od_pro_csv", "FD_MOBPRO_2019.csv")
    context.config("od_sco_csv", "FD_MOBSCO_2019.csv")

def execute(context):
    df_codes = context.stage("data.spatial.codes")
    requested_communes = list(map(str, df_codes["commune_id"].unique()))

    # First, load work
    COLUMNS_DTYPES = {
        "COMMUNE": pl.String,
        "ARM": pl.String,
        "TRANS": pl.Int64,
        "IPONDI": pl.Float64,
        "DCLT": pl.String,
    }

    with zipfile.ZipFile(
        os.path.join(context.config("data_path"), context.config("od_pro_path"))
    ) as archive:
        with archive.open(context.config("od_pro_csv")) as f:
            work = pl.read_csv(
                f.read(),
                separator=";",
                columns=list(COLUMNS_DTYPES.keys()),
                schema_overrides=COLUMNS_DTYPES,
            )
    work = work.filter(
        (pl.col("COMMUNE").is_in(requested_communes) | pl.col("ARM").is_in(requested_communes))
        & pl.col("DCLT").is_in(requested_communes)
    )

    # Second, load education
    COLUMNS_DTYPES = {
        "COMMUNE": pl.String,
        "ARM": pl.String,
        "IPONDI": pl.Float64,
        "DCETUF": pl.String,
        "AGEREV10": pl.Int64,
    }

    with zipfile.ZipFile(
        os.path.join(context.config("data_path"), context.config("od_sco_path"))
    ) as archive:
        with archive.open(context.config("od_sco_csv")) as f:
            education = pl.read_csv(
                f.read(),
                separator=";",
                columns=list(COLUMNS_DTYPES.keys()),
                schema_overrides=COLUMNS_DTYPES
            )
    education = education.filter(
        (pl.col("COMMUNE").is_in(requested_communes) | pl.col("ARM").is_in(requested_communes))
        & pl.col("DCETUF").is_in(requested_communes)
    )

    return work.to_pandas(), education.to_pandas()


def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("od_pro_path"))):
        raise RuntimeError("RP MOBPRO data is not available")

    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("od_sco_path"))):
        raise RuntimeError("RP MOBSCO data is not available")

    return [
        os.path.getsize("%s/%s" % (context.config("data_path"), context.config("od_pro_path"))),
        os.path.getsize("%s/%s" % (context.config("data_path"), context.config("od_sco_path")))
    ]
