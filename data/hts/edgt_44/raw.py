from pandas.core.frame import DataFrame
import numpy as np
import pandas as pd
import geopandas as gpd
import os

"""
This stage loads the raw data of the specified HTS (EDGT Loire Atlantique).

Adapted from the first implementation by Valentin Le Besond (IFSTTAR Nantes)
"""


def configure(context):
    context.config("data_path")


from .format import HOUSEHOLD_FORMAT, PERSON_FORMAT, TRIP_FORMAT

HOUSEHOLD_COLUMNS = {
    "MP2": str,
    "MTIR": str,
    "ECH": str,
    "COEM": float,
    "M6": int,
    "M7": int,
    "M5": int,
}

PERSON_COLUMNS = {
    "ECH": str,
    "PTIR": str,
    "PER": int,
    "PP2": str,
    "PENQ": int,
    "P3": int,
    "P2": int,
    "P4": int,
    "P7": str,
    "P12": str,
    "P9": str,
    "P5": str,
    "COEP": float,
    "COEQ": float,
    "P1": int,
}

TRIP_COLUMNS = {
    "ECH": str,
    "DTIR": str,
    "PER": int,
    "NDEP": int,
    "DP2": str,
    "D2A": int,
    "D5A": int,
    "D3": str,
    "D4A": int,
    "D4B": int,
    "D7": str,
    "D8A": int,
    "D8B": int,
    "D8C": int,
    "MODP": int,
    "DOIB": int,
    "DIST": int,
}


def execute(context):
    # Load households
    df_household_dictionary = pd.DataFrame.from_records(
        HOUSEHOLD_FORMAT, columns=["position", "size", "variable", "description"]
    )

    column_widths = df_household_dictionary["size"].values
    column_names = df_household_dictionary["variable"].values

    df_households = pd.read_fwf(
        "%s/edgt_44_2015/02a_EDGT_44_MENAGE_FAF_TEL_2015-08-07_modifZF.txt"
        % context.config("data_path"),
        widths=column_widths,
        header=None,
        names=column_names,
        usecols=list(HOUSEHOLD_COLUMNS.keys()),
        dtype=HOUSEHOLD_COLUMNS,
    )

    # Load persons
    df_person_dictionary = pd.DataFrame.from_records(
        PERSON_FORMAT, columns=["position", "size", "variable", "description"]
    )

    column_widths = df_person_dictionary["size"].values
    column_names = df_person_dictionary["variable"].values

    df_persons = pd.read_fwf(
        "%s/edgt_44_2015/02b_EDGT_44_PERSO_FAF_TEL_ModifPCS_2016-04-14.txt"
        % context.config("data_path"),
        widths=column_widths,
        header=None,
        names=column_names,
        usecols=list(PERSON_COLUMNS.keys()),
        dtype=PERSON_COLUMNS,
    )

    # Load trips
    df_trip_dictionary = pd.DataFrame.from_records(
        TRIP_FORMAT, columns=["position", "size", "variable", "description"]
    )

    column_widths = df_trip_dictionary["size"].values
    column_names = df_trip_dictionary["variable"].values

    df_trips = pd.read_fwf(
        "%s/edgt_44_2015/02c_EDGT_44_DEPLA_FAF_TEL_DIST_2015-11-10.txt"
        % context.config("data_path"),
        widths=column_widths,
        header=None,
        names=column_names,
        usecols=list(TRIP_COLUMNS.keys()),
        dtype=TRIP_COLUMNS,
    )

    return df_households, df_persons, df_trips


FILES = [
    "02a_EDGT_44_MENAGE_FAF_TEL_2015-08-07_modifZF.txt",
    "02b_EDGT_44_PERSO_FAF_TEL_ModifPCS_2016-04-14.txt",
    "02c_EDGT_44_DEPLA_FAF_TEL_DIST_2015-11-10.txt",
]


def validate(context):
    for name in FILES:
        if not os.path.exists(
            "%s/edgt_44_2015/%s" % (context.config("data_path"), name)
        ):
            raise RuntimeError("File missing from EDGT: %s" % name)

    return [
        os.path.getsize("%s/edgt_44_2015/%s" % (context.config("data_path"), name))
        for name in FILES
    ]
