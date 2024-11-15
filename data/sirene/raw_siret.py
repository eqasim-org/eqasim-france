import os
import pandas as pd

"""
This stage loads the raw data from the French enterprise registry.
"""


def configure(context):
    context.config("data_path")
    context.config("siret_path", "sirene/StockEtablissement_utf8.zip")

    context.stage("data.spatial.codes")


def execute(context):
    # Filter by departement
    df_codes = context.stage("data.spatial.codes")
    requested_departements = set(df_codes["departement_id"].unique())

    df_siret = []

    COLUMNS_DTYPES = {
        "siren": "int32",
        "siret": "int64",
        "codeCommuneEtablissement": "str",
        "activitePrincipaleEtablissement": "str",
        "trancheEffectifsEtablissement": "str",
        "etatAdministratifEtablissement": "str",
    }

    with context.progress(label="Reading SIRET...") as progress:
        csv = pd.read_csv(
            "%s/%s" % (context.config("data_path"), context.config("siret_path")),
            usecols=COLUMNS_DTYPES.keys(),
            dtype=COLUMNS_DTYPES,
            chunksize=10240,
        )

        for df_chunk in csv:
            progress.update(len(df_chunk))

            f = df_chunk["codeCommuneEtablissement"].isna()  # Just to get a mask

            for departement in requested_departements:
                f |= df_chunk["codeCommuneEtablissement"].str.startswith(departement)

            f &= ~df_chunk["codeCommuneEtablissement"].isna()
            df_chunk = df_chunk[f]

            if len(df_chunk) > 0:
                df_siret.append(df_chunk)

    return pd.concat(df_siret)


def validate(context):
    if not os.path.exists(
        "%s/%s" % (context.config("data_path"), context.config("siret_path"))
    ):
        raise RuntimeError("SIRENE: SIRET data is not available")

    return os.path.getsize(
        "%s/%s" % (context.config("data_path"), context.config("siret_path"))
    )
