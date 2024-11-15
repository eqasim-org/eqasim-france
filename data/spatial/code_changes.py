import os
import pandas as pd

"""
This stages loads a file containing all spatial codes in France and how
they can be translated into each other. This particular stage loads information
on how old identifiers can be translated into newer ones.
"""

YEAR = 2021
SOURCE = "codes_%d/reference_IRIS_geo%d.xlsx" % (YEAR, YEAR)


def configure(context):
    context.config("data_path")

    context.config("regions", [11])
    context.config("departments", [])


def execute(context):
    # Load IRIS registry
    df_modifications = pd.read_excel(
        "%s/%s" % (context.config("data_path"), SOURCE),
        skiprows=5,
        sheet_name="Modifications_IRIS",
    )[["IRIS_INI", "IRIS_FIN", "COM_INI", "COM_FIN"]].rename(
        columns={
            "IRIS_INI": "initial_iris",
            "IRIS_FIN": "final_iris",
            "COM_INI": "initial_commune",
            "COM_FIN": "final_commune",
        }
    )

    df_modifications["initial_iris"] = df_modifications["initial_iris"].astype(
        "category"
    )
    df_modifications["final_iris"] = df_modifications["final_iris"].astype("category")
    df_modifications["initial_commune"] = df_modifications["initial_commune"].astype(
        "category"
    )
    df_modifications["final_commune"] = df_modifications["final_commune"].astype(
        "category"
    )

    return df_modifications


def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), SOURCE)):
        raise RuntimeError("Spatial reference codes are not available")

    return os.path.getsize("%s/%s" % (context.config("data_path"), SOURCE))


def update(df_changes, level, values):
    initial_slot = "initial_%s" % level
    final_slot = "final_%s" % level

    df_source = df_changes[df_changes[initial_slot].isin(values.unique())]
    dictionary = {k: v for k, v in zip(df_source[initial_slot], df_source[final_slot])}

    if len(dictionary) > 0:
        print("Updating %d deprecated zone identifiers ..." % len(dictionary))

    return values.replace(dictionary)
