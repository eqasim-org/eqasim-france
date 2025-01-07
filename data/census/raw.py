import pandas as pd
import os
import zipfile

"""
This stage loads the raw data from the French population census.
"""

def configure(context):
    context.stage("data.spatial.codes")

    context.config("data_path")
    context.config("census_path", "rp_2021/RP2021_indcvi.zip")
    context.config("census_csv", "FD_INDCVI_2021.csv")

    context.config("projection_year", None)

COLUMNS_DTYPES = {
    "CANTVILLE":"str", 
    "NUMMI":"str", 
    "AGED":"str",
    "COUPLE":"str", 
    "CS1":"str",
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

    # only pre-filter if we don't need to reweight the census later
    prefilter_departments = context.config("projection_year") is None

    with context.progress(label = "Reading census ...") as progress:
        with zipfile.ZipFile(
            "{}/{}".format(context.config("data_path"), context.config("census_path"))) as archive:
            with archive.open(context.config("census_csv")) as f:
                csv = pd.read_csv(f, 
                        usecols = COLUMNS_DTYPES.keys(), sep = ";",
                        dtype = COLUMNS_DTYPES,
                        chunksize = 10240)
    
                for df_chunk in csv:
                    progress.update(len(df_chunk))
                    
                    if prefilter_departments:
                        df_chunk = df_chunk[df_chunk["DEPT"].isin(requested_departements)]

                    if len(df_chunk) > 0:
                        df_records.append(df_chunk)

    return pd.concat(df_records)


def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("census_path"))):
        raise RuntimeError("RP 2021 data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("census_path")))
