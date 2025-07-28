import polars as pl
import os
import zipfile

"""
This stage loads the raw data from the French population census.
"""

def configure(context):
    context.stage("data.spatial.codes")

    context.config("data_path")
    context.config("census_path", "rp_2019/RP2019_INDCVI_csv.zip")
    context.config("census_csv", "FD_INDCVI_2019.csv")

    context.config("projection_year", None)

COLUMNS_DTYPES = {
    "CANTVILLE": pl.String,
    "NUMMI": pl.String,
    "AGED": pl.String,
    "COUPLE": pl.String,
    "CS1": pl.String,
    "DEPT": pl.String,
    "ETUD": pl.String,
    "IPONDI": pl.String,
    "IRIS": pl.String,
    "REGION": pl.String,
    "SEXE": pl.String,
    "TACT": pl.String,
    "TRANS": pl.String,
    "VOIT": pl.String,
    "DEROU": pl.String,
}

def execute(context):
    df_codes = context.stage("data.spatial.codes")

    # only pre-filter if we don't need to reweight the census later
    prefilter_departments = context.config("projection_year") is None

    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("census_path"))) as archive:
        with archive.open(context.config("census_csv")) as f:
            df = pl.read_csv(
                f.read(), 
                separator=";",
                columns=list(COLUMNS_DTYPES.keys()),
                schema_overrides=COLUMNS_DTYPES,
            )
            if prefilter_departments:
                requested_departements = list(map(str, df_codes["departement_id"].unique()))
                df = df.filter(pl.col("DEPT").is_in(requested_departements))
    return df.to_pandas()


def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("census_path"))):
        raise RuntimeError("RP 2019 data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("census_path")))
