import os
import polars as pl

"""
This stage loads the raw data from the French population census.
"""

def configure(context):
    context.stage("data.spatial.codes")

    context.config("data_path")
    context.config("census_path", "rp_2022/RP2022_indcvi.parquet")

    context.config("census.attributes", {})

COLUMNS = {
    "CANTVILLE",
    "NUMMI",
    "AGEREV",
    "COUPLE",
    "GS",
    "STAT_GSEC",
    "DEPT",
    "ETUD",
    "IPONDI",
    "IRIS",
    "REGION",
    "SEXE",
    "TACT",
    "TP",
    "TRANS",
    "VOIT",
    "DEROU"
}


def execute(context):
    df_codes = context.stage("data.spatial.codes")

    requested_departements = df_codes["departement_id"].unique()

    with context.progress(label = "Reading census ...") as progress:
        selected_columns = COLUMNS + list(sorted(context.config("census.attributes", {}).keys()))
        
        parquet = pl.read_parquet( "{}/{}".format(context.config("data_path"), context.config("census_path")),
                        columns=selected_columns)

        parquet = parquet.cast(pl.String)
        parquet = parquet.filter(pl.col("DEPT").is_in(requested_departements))

        progress.update(len(parquet))


    return parquet.to_pandas()

def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("census_path"))):
        raise RuntimeError("RP 2022 data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("census_path")))
