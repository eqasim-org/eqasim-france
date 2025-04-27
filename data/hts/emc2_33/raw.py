import pandas as pd
import os

"""
This stage loads the raw data of the specified HTS (EMC2 Gironde).
"""

def configure(context):
    context.config("data_path")

HOUSEHOLD_COLUMNS = {
    "MP2": str, "ECH": str, "COEM": float,
    "M14": int, "M20": int, "M5": int
}

PERSON_COLUMNS = {
    "ECH": str, "PER": int, "PP2": str, "PENQ": int,
    "P3": int, "P2": int, "P4": int,
    "P7": str, "P10": str, "P12": str,
    "P9": str, "P5": str,
    "COEP": float, "COEQ": float
}

TRIP_COLUMNS = {
    "ECH": str, "PER": int, "NDEP": int, "DP2": str,
    "D2A": int, "D5A": int, "D3": int, "D4": str,
    "D7": int, "D8": str,
    "D8C": int, "MODP": int, "DOIB": int, "DIST": int
}

def execute(context):
    # Load households
    df_households = pd.read_csv(
        "%s/emc2_33_2021/08a_EMC2_Gironde_2022_Men_Fusion_men2021_MQPV_23052023.csv"
        % context.config("data_path"),
        usecols = list(HOUSEHOLD_COLUMNS.keys()), dtype = HOUSEHOLD_COLUMNS,sep=";"
    )

    # Load persons
    df_persons = pd.read_csv(
        "%s/emc2_33_2021/07b_EMC2_Gironde_2022_Pers_Fusion_men2021_P19A_13022023.csv"
     % context.config("data_path"),
     usecols = list(PERSON_COLUMNS.keys()), dtype = PERSON_COLUMNS,sep=";"
 )

    # Load trips
    df_trips = pd.read_csv(
        "%s/emc2_33_2021/07c_EMC2_Gironde_2022_Depl_Fusion_men2021_D11_03022023.csv"
        % context.config("data_path"),
        usecols = list(TRIP_COLUMNS.keys()), dtype = TRIP_COLUMNS,sep=";"
    )

    return df_households, df_persons, df_trips

FILES = [
    "08a_EMC2_Gironde_2022_Men_Fusion_men2021_MQPV_23052023.csv",
    "07b_EMC2_Gironde_2022_Pers_Fusion_men2021_P19A_13022023.csv",
    "07c_EMC2_Gironde_2022_Depl_Fusion_men2021_D11_03022023.csv",
]

def validate(context):
    for name in FILES:
        if not os.path.exists("%s/emc2_33_2021/%s" % (context.config("data_path"), name)):
            raise RuntimeError("File missing from EDGT: %s" % name)

    return [
        os.path.getsize("%s/emc2_33_2021/%s" % (context.config("data_path"), name))
        for name in FILES
    ]
