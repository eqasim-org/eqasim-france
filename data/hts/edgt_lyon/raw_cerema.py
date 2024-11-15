from pandas.core.frame import DataFrame
import numpy as np
import pandas as pd
import geopandas as gpd
import os

"""
This stage loads the raw data of the specified HTS (EDGT Lyon).

Adapted from the first implementation by Valentin Le Besond (IFSTTAR Nantes)
"""


def configure(context):
    context.config("data_path")


HOUSEHOLD_COLUMNS = {
    "MP2": str,
    "ECH": str,
    "COEM": float,
    "M6": int,
    "M7": int,
    "M5": int,
}

PERSON_COLUMNS = {
    "ECH": str,
    "PER": int,
    "PP2": str,
    "PENQ": str,
    "P3": int,
    "P2": int,
    "P4": int,
    "P7": str,
    "P12": str,
    "P10": str,
    "P9": str,
    "P5": str,
    "COEP": float,
    "COEQ": float,
    "P1": int,
}

TRIP_COLUMNS = {
    "ECH": str,
    "PER": int,
    "NDEP": int,
    "DP2": str,
    "D2A": int,
    "D5A": int,
    "D3": str,
    "D4": int,
    "D7": str,
    "D8": int,
    "D8C": int,
    "MODP": int,
    "DOIB": int,
    "DIST": int,
}


def execute(context):
    # Load households
    df_household_dictionary = pd.read_excel(
        "%s/edgt_lyon_2015/EDGT-AML-2015_Total_Dessin&Dictionnaire.xls"
        % context.config("data_path"),
        skiprows=1,
        nrows=21,
        usecols=[1, 2],
        names=["size", "variable"],
    )

    column_widths = df_household_dictionary["size"].values
    column_names = df_household_dictionary["variable"].values

    df_households = pd.read_fwf(
        "%s/edgt_lyon_2015/EDGT_AML_MENAGE_FAF_TEL_2015-08-03.txt"
        % context.config("data_path"),
        widths=column_widths,
        header=None,
        names=column_names,
        usecols=list(HOUSEHOLD_COLUMNS.keys()),
        dtype=HOUSEHOLD_COLUMNS,
    )

    # Load persons
    df_person_dictionary = pd.read_excel(
        "%s/edgt_lyon_2015/EDGT-AML-2015_Total_Dessin&Dictionnaire.xls"
        % context.config("data_path"),
        skiprows=25,
        nrows=34,
        usecols=[1, 2],
        names=["size", "variable"],
    )

    column_widths = df_person_dictionary["size"].values
    column_names = df_person_dictionary["variable"].values

    df_persons = pd.read_fwf(
        "%s/edgt_lyon_2015/EDGT_AML_PERSO_DIST_DT_2015-10-27.txt"
        % context.config("data_path"),
        widths=column_widths,
        header=None,
        names=column_names,
        usecols=list(PERSON_COLUMNS.keys()),
        dtype=PERSON_COLUMNS,
    )

    # Load trips
    df_trip_dictionary = pd.read_excel(
        "%s/edgt_lyon_2015/EDGT-AML-2015_Total_Dessin&Dictionnaire.xls"
        % context.config("data_path"),
        skiprows=62,
        nrows=24,
        usecols=[1, 2],
        names=["size", "variable"],
    )

    column_widths = df_trip_dictionary["size"].values
    column_names = df_trip_dictionary["variable"].values

    df_trips = pd.read_fwf(
        "%s/edgt_lyon_2015/EDGT_AML_DEPLA_DIST_2015-10-27.txt"
        % context.config("data_path"),
        widths=column_widths,
        header=None,
        names=column_names,
        usecols=list(TRIP_COLUMNS.keys()),
        dtype=TRIP_COLUMNS,
    )

    # Load spatial data
    df_spatial = gpd.read_file(
        "%s/edgt_lyon_2015/EDGT_AML2015_ZF_GT.TAB" % context.config("data_path")
    )

    return df_households, df_persons, df_trips, df_spatial


FILES = [
    "EDGT_AML_MENAGE_FAF_TEL_2015-08-03.txt",
    "EDGT_AML_PERSO_DIST_DT_2015-10-27.txt",
    "EDGT_AML_DEPLA_DIST_2015-10-27.txt",
    "EDGT-AML-2015_Total_Dessin&Dictionnaire.xls",
    "EDGT_AML2015_ZF_GT.DAT",
    "EDGT_AML2015_ZF_GT.ID",
    "EDGT_AML2015_ZF_GT.IND",
    "EDGT_AML2015_ZF_GT.MAP",
    "EDGT_AML2015_ZF_GT.TAB",
]


def validate(context):
    for name in FILES:
        if not os.path.exists(
            "%s/edgt_lyon_2015/%s" % (context.config("data_path"), name)
        ):
            raise RuntimeError("File missing from EDGT: %s" % name)

    return [
        os.path.getsize("%s/edgt_lyon_2015/%s" % (context.config("data_path"), name))
        for name in FILES
    ]
