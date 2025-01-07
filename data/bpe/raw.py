import pandas as pd
import os
import zipfile

"""
This stage loads the raw data from the French service registry.
"""

def configure(context):
    context.config("data_path")
    context.config("bpe_path", "bpe_2023/BPE23.zip")
    context.config("bpe_csv", "BPE23.csv")
    context.stage("data.spatial.codes")

def execute(context):
    df_records = []

    df_codes = context.stage("data.spatial.codes")
    requested_departements = df_codes["departement_id"].unique()

    with context.progress(label = "Reading BPE ...") as progress:
        with zipfile.ZipFile("{}/{}".format(context.config("data_path"), context.config("bpe_path"))) as archive:
            with archive.open(context.config("bpe_csv")) as f:
                csv = pd.read_csv(f, usecols = [
                        "DCIRIS", "LAMBERT_X", "LAMBERT_Y",
                        "TYPEQU", "DEPCOM", "DEP"
                    ], sep = ";",
                    dtype = dict(DEPCOM = str, DEP = str, DCIRIS = str),
                    chunksize = 10240
                )

                for df_chunk in csv:
                    progress.update(len(df_chunk))

                    df_chunk = df_chunk[df_chunk["DEP"].isin(requested_departements)]

                    if len(df_chunk) > 0:
                        df_records.append(df_chunk)

    return pd.concat(df_records)

def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("bpe_path"))):
        raise RuntimeError("BPE data is not available")

    return os.path.getsize("%s/%s" % (context.config("data_path"), context.config("bpe_path")))
