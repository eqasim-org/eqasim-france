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
    "ECH": str, "ZFM": str, # id
    "M6": int, "M21": int, "M14": int,  # number_of_cars, number_of_bicycles, number_of_motorbikes
    "COE0": float # weights
}

PERSON_COLUMNS = {
    "ECH": str, "PER": int, "ZFP": str, # id
    "PENQ": str, # respondents of travel questionary section
    "P2": int, "P4": int, # sex, age
    "P9": str, # employed, studies
    "P7": str, "P12": str, # has_license, has_pt_subscription
    "PCSC": str, # socioprofessional_class
    "COEP": float, "COE1": float # weights
}

TRIP_COLUMNS = {
    "ECH": str, "PER": int, "NDEP": int, "ZFD": str, # id
    "D2A": int, "D5A": int, # preceding_purpose, following_purpose
    "D3": str, "D7": str, # origin_zone, destination_zone
    "D4": int, "D8": int, # time_departure, time_arrival
    "MODP": int, "D11": int, "D12": int # mode, euclidean_distance, routed_distance
}

def execute(context):
    # Load households
    df_households = pd.concat([
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_std_faf_men.csv"
            % context.config("data_path"), sep=";", usecols = list(HOUSEHOLD_COLUMNS.keys()), dtype = HOUSEHOLD_COLUMNS
        ),
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_std_tel_men.csv"
            % context.config("data_path"), sep=";", usecols = list(HOUSEHOLD_COLUMNS.keys()), dtype = HOUSEHOLD_COLUMNS
        )
    ])

    # Load persons
    df_persons = pd.concat([
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_std_faf_pers.csv"
            % context.config("data_path"), sep=";", usecols = list(PERSON_COLUMNS.keys()), dtype = PERSON_COLUMNS
        ),
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_std_tel_pers.csv"
            % context.config("data_path"), sep=";", usecols = list(PERSON_COLUMNS.keys()), dtype = PERSON_COLUMNS
        )
    ])

    # Load trips
    df_trips = pd.concat([
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_std_faf_depl.csv"
            % context.config("data_path"), sep=";", usecols = list(TRIP_COLUMNS.keys()), dtype = TRIP_COLUMNS
        ),
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_std_tel_depl.csv"
            % context.config("data_path"), sep=";", usecols = list(TRIP_COLUMNS.keys()), dtype = TRIP_COLUMNS
        )
    ])

    # Load spatial data
    df_spatial = gpd.read_file(
        "%s/edgt_lyon_2015/EDGT_AML2015_ZF_GT.TAB"
        % context.config("data_path"))

    return df_households, df_persons, df_trips, df_spatial

FILES = [
    "lyon_2015_std_faf_men.csv",
    "lyon_2015_std_tel_men.csv",
    "lyon_2015_std_faf_pers.csv",
    "lyon_2015_std_tel_pers.csv",
    "lyon_2015_std_faf_traj.csv",
    "lyon_2015_std_tel_traj.csv",
    "EDGT_AML2015_ZF_GT.DAT",
    "EDGT_AML2015_ZF_GT.ID",
    "EDGT_AML2015_ZF_GT.IND",
    "EDGT_AML2015_ZF_GT.MAP",
    "EDGT_AML2015_ZF_GT.TAB"
]

def validate(context):
    for name in FILES:
        if not os.path.exists("%s/edgt_lyon_2015/%s" % (context.config("data_path"), name)):
            raise RuntimeError("File missing from EDGT: %s" % name)

    return [
        os.path.getsize("%s/edgt_lyon_2015/%s" % (context.config("data_path"), name))
        for name in FILES
    ]
