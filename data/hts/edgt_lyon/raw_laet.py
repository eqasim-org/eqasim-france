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
    "ech": str, "zfm": str, # id
    "m6": int, "m21": int, "m14": int,  # number_of_cars, number_of_bikes, number_of_motorbikes
    "coem": float # weights
}

PERSON_COLUMNS = {
    "ech": str, "per": int, "zfp": str, # id
    "penq": str, # respondents of travel questionary section
    "p2": int, "p4": int, # sex, age
    "p9": str, # employed, studies
    "p7": str, "p12": str, # has_license, has_pt_subscription
    "p11": str,"dp15":int, # socioprofessional_class
    "coep": float, "coeq": float # weights
}

TRIP_COLUMNS = {
    "ech": str, "per": int, "ndep": int, "zfd": str, # id
    "d2a": int, "d5a": int, # preceding_purpose, following_purpose
    "d3": str, "d7": str, # origin_zone, destination_zone
    "d4": int, "d8": int, # time_departure, time_arrival
    "modp": int, "doib": int, "dist": int # mode, euclidean_distance, routed_distance
}

def execute(context):
    # Load households
    df_households = pd.concat([
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_ori_faf_men.csv"
            % context.config("data_path"), sep=";", usecols = list(HOUSEHOLD_COLUMNS.keys()), dtype = HOUSEHOLD_COLUMNS
        ),
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_ori_tel_men.csv"
            % context.config("data_path"), sep=";", usecols = list(HOUSEHOLD_COLUMNS.keys()), dtype = HOUSEHOLD_COLUMNS
        )
    ])
    df_households.columns = df_households.columns.str.upper()
    
    # Load persons
    df_persons = pd.concat([
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_ori_faf_pers.csv"
            % context.config("data_path"), sep=";", usecols = list(set(PERSON_COLUMNS.keys()) - set(["penq"])), dtype = PERSON_COLUMNS
        ),
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_ori_tel_pers.csv"
            % context.config("data_path"), sep=";", usecols = list(PERSON_COLUMNS.keys()) , dtype = PERSON_COLUMNS
        )
    ])
    df_persons.columns = df_persons.columns.str.upper()
    
    # Load trips
    df_trips = pd.concat([
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_ori_faf_depl.csv"
            % context.config("data_path"), sep=";", usecols = list(TRIP_COLUMNS.keys()), dtype = TRIP_COLUMNS
        ),
        pd.read_csv(
            "%s/edgt_lyon_2015/lyon_2015_ori_tel_depl.csv"
            % context.config("data_path"), sep=";", usecols = list(TRIP_COLUMNS.keys()), dtype = TRIP_COLUMNS
        )
    ])
    df_trips.columns = df_trips.columns.str.upper()
    
    # Load spatial data
    df_spatial = gpd.read_file(
        "%s/edgt_lyon_2015/EDGT_AML2015_ZF_GT.TAB"
        % context.config("data_path"))

    return df_households, df_persons, df_trips, df_spatial

FILES = [
    "lyon_2015_ori_faf_men.csv",
    "lyon_2015_ori_tel_men.csv",
    "lyon_2015_ori_faf_pers.csv",
    "lyon_2015_ori_tel_pers.csv",
    "lyon_2015_ori_faf_depl.csv",
    "lyon_2015_ori_tel_depl.csv",
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
