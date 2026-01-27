import pandas as pd
import os
import zipfile
import pyarrow as pa
import polars as pl
"""
Loads raw OD data from French census data.
"""

def configure(context):
    context.stage("data.spatial.codes")
    context.config("data_path")
    context.config("od_pro_path", "rp_2022/RP2022_mobpro.parquet")
    context.config("od_sco_path", "rp_2022/RP2022_mobsco.parquet")

def execute(context):
    df_codes = context.stage("data.spatial.codes")
    requested_communes = df_codes["commune_id"].unique()

    # First, load work
    with context.progress(label = "Reading work flows ...") as progress:
        df_records = []

        COLUMNS_DTYPES = {
            "COMMUNE":pl.String, 
            "ARM":pl.String, 
            "TRANS":pl.Int32,
            "IPONDI":pl.Float32, 
            "DCLT":pl.String
        }

        parquet = pl.read_parquet("{}/{}".format(context.config("data_path"), context.config("od_pro_path")),columns=  list(COLUMNS_DTYPES.keys()),
                                  )
        
        parquet = parquet.cast(COLUMNS_DTYPES)
        parquet = parquet.filter(((pl.col("COMMUNE").is_in(requested_communes))|(pl.col("ARM").is_in(requested_communes)))&(pl.col("DCLT").is_in(requested_communes)))
        
        progress.update(len(parquet))

    work = parquet.to_pandas()

    # Second, load education
    with context.progress(label = "Reading education flows ...") as progress:
        df_records = []

        COLUMNS_DTYPES = {
            "COMMUNE":pl.String, 
            "ARM":pl.String, 
            "IPONDI":pl.Float32,
            "DCETUF":pl.String,
            "AGEREV10":pl.String
        }

        parquet = pl.read_parquet("{}/{}".format(context.config("data_path"), context.config("od_sco_path")), columns=  COLUMNS_DTYPES.keys(), 
                                  )

        parquet = parquet.filter(((pl.col("COMMUNE").is_in(requested_communes))|(pl.col("ARM").is_in(requested_communes)))&(pl.col("DCETUF").is_in(requested_communes)))
        parquet = parquet.cast(COLUMNS_DTYPES)

        progress.update(len(parquet))

    education = parquet.to_pandas()

    return work, education


def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("od_pro_path"))):
        raise RuntimeError("RP MOBPRO data is not available")

    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("od_sco_path"))):
        raise RuntimeError("RP MOBSCO data is not available")

    return [
        os.path.getsize("%s/%s" % (context.config("data_path"), context.config("od_pro_path"))),
        os.path.getsize("%s/%s" % (context.config("data_path"), context.config("od_sco_path")))
    ]
