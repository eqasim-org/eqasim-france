import pandas as pd
import os
import zipfile
import pyarrow as pa
import polars as pl
"""
This stage loads the raw data from the French population census.
"""

def configure(context):
    context.stage("data.spatial.codes")

    context.config("data_path")
    context.config("census_path", "rp_2022/RP2022_indcvi.parquet")
    #context.config("census_csv", "FD_INDCVI_2021.csv")

COLUMNS_DTYPES = {
    "CANTVILLE":"str", 
    "NUMMI":"str", 
    "AGED":"str",
    "COUPLE":"str", 
    "GS":"str",
    "DEPT":"str", 
    "ETUD":"str",
    "IPONDI":"str", 
    "IRIS":"str",
    "REGION":"str", 
    "SEXE":"str",
    "TACT":"str", 
    "TRANS":"str",
    "VOIT":"str", 
    "DEROU":"str"
}


def execute(context):
    df_records = []
    df_codes = context.stage("data.spatial.codes")

    requested_departements = df_codes["departement_id"].unique()

    with context.progress(label = "Reading census ...") as progress:
        parquet = pl.read_parquet( "{}/{}".format(context.config("data_path"), context.config("census_path")),
                        columns=  COLUMNS_DTYPES.keys())
        
        parquet = parquet.cast(pl.String)
        parquet = parquet.filter(pl.col("DEPT").is_in(requested_departements))

        progress.update(len(parquet))
                    

    return parquet.to_pandas()

def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("census_path"))):
        raise RuntimeError("RP 2022 data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("census_path")))
