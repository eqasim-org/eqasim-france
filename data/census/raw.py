import os
import polars as pl

"""
This stage loads the raw data from the French population census.
"""

def configure(context):
    context.stage("data.spatial.codes")

    context.config("data_path")
    context.config("census_path", "rp_2022/RP2022_indcvi.parquet")

    context.config("census_attributes", [])

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

    requested_iris = df_codes["iris_id"].unique()
    requested_communes = df_codes["commune_id"].unique()
    requested_departements = df_codes["departement_id"].unique()
    census_attributes = { attribute["raw"] for attribute in context.config("census_attributes") }

    with context.progress(label = "Reading census ...") as progress:
        parquet = pl.read_parquet( "{}/{}".format(context.config("data_path"), context.config("census_path")),
                        columns=COLUMNS | census_attributes)

        parquet = parquet.cast(pl.String)
        if len(requested_iris) > 0:
            parquet = parquet.filter(pl.col("IRIS").is_in(requested_iris))
        elif len(requested_communes) > 0:
            parquet = parquet.filter(pl.col("IRIS").str.slice(0, 5).is_in(requested_communes))
        else:
            parquet = parquet.filter(pl.col("DEPT").is_in(requested_departements))

        progress.update(len(parquet))


    return parquet.to_pandas()

def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("census_path"))):
        raise RuntimeError("RP 2022 data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("census_path")))
