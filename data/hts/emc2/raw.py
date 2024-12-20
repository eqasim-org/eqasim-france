import pandas as pd
import geopandas as gpd
import os

"""
This stage loads the raw data of the specified HTS (generic EMC2).

Adapted from the first implementation by Valentin Le Besond (IFSTTAR Nantes)
"""


def configure(context):
    context.config("data_path")
    context.config("hts_path")


HOUSEHOLD_COLUMNS = {
    "METH": str, # survey method
    "ECH": str,  # household_id
    "ZFM": int,  # zone_id
    "M6": int,  # number_of_cars
    "M21": int,  # number_of_bikes
    "M14": int,  # number_of_motorbikes
    "COE0": float,  # weights
}

PERSON_COLUMNS = {
    "PMET": str, # survey method
    "ECH": str,  # household_id
    "PER": int,  # person_id
    "ZFP": int,  # zone_id
    "PENQ": str,  # respondents of travel questionary section
    "P2": int,  # sex
    "P4": int,  # age
    "P9": str,  # employed, studies
    "P7": str,  # has_license
    "P12": str,  # has_pt_subscription
    "PCSC": str,  # socioprofessional_class
    "COEP": float,  # weights (surveyed)
    "COE1": float,  # weights (all)
}

TRIP_COLUMNS = {
    "DMET": str, # survey method
    "ECH": str,  # household_id
    "PER": int,  # person_id
    "NDEP": int,  # trip_id
    "ZFD": int,  # zone_id
    "D2A": int,  # preceding_purpose
    "D5A": int,  # following_purpose
    "D3": int,  # origin_zone
    "D7": int,  # destination_zone
    "D4": int,  # time_departure
    "D8": int,  # time_arrival
    "MODP": int,  # mode
    "D11": int,  # euclidean_distance
    "D12": int,  # routed_distance
}


def execute(context):
    # The EMC2 files are stored in the directory `Csv/Fichiers_Standard/` but the name of the city
    # is in the filename (e.g., `chambery_2022_std_depl.csv`) so the files are found based on the
    # last part of the filename.
    # Note. If there are multiple files matching "_men.csv", only the first one will be read.
    emc_dir = os.path.join(context.config("data_path"), context.config("hts_path"))
    csv_dir = os.path.join(emc_dir, "Csv", "Fichiers_Standard")
    filelist = os.listdir(csv_dir)
    # Load households
    household_filename = next(filter(lambda n: n.endswith("_men.csv"), filelist))
    df_households = pd.read_csv(
        os.path.join(csv_dir, household_filename),
        sep=";",
        usecols=list(HOUSEHOLD_COLUMNS.keys()),
        dtype=HOUSEHOLD_COLUMNS,
    )

    # Load persons
    person_filename = next(filter(lambda n: n.endswith("_pers.csv"), filelist))
    df_persons = pd.read_csv(
        os.path.join(csv_dir, person_filename),
        sep=";",
        usecols=list(PERSON_COLUMNS.keys()),
        dtype=PERSON_COLUMNS,
    )

    # Load trips
    trip_filename = next(filter(lambda n: n.endswith("_depl.csv"), filelist))
    df_trips = pd.read_csv(
        os.path.join(csv_dir, trip_filename),
        sep=";",
        usecols=list(TRIP_COLUMNS.keys()),
        dtype=TRIP_COLUMNS,
    )

    # Load spatial data
    # The file describing the zones is a shapefile or TAB file stored in `Doc/SIG/`.
    sig_dir = os.path.join(emc_dir, "Doc", "SIG")
    filelist = os.listdir(sig_dir)
    zf_filename = next(filter(lambda n: "_ZF" in n and n[-3:].lower() in ("shp", "tab"), filelist))
    df_spatial = gpd.read_file(os.path.join(sig_dir, zf_filename))
    df_spatial["ZF"] = df_spatial["ZF"].astype(int)

    return df_households, df_persons, df_trips, df_spatial


def validate(context):
    # The EMC2 files are stored in the directory `Csv/Fichiers_Standard/` but the name of the city
    # is in the filename (e.g., `chambery_2022_std_depl.csv`) so we check the file exist based on
    # the last part of the filename.
    emc_dir = os.path.join(context.config("data_path"), context.config("hts_path"))
    csv_dir = os.path.join(emc_dir, "Csv", "Fichiers_Standard")
    filelist = os.listdir(csv_dir)
    men_size = None
    pers_size = None
    depl_size = None
    for name in filelist:
        if name.endswith("_men.csv"):
            men_size = os.path.getsize(os.path.join(csv_dir, name))
        elif name.endswith("_pers.csv"):
            pers_size = os.path.getsize(os.path.join(csv_dir, name))
        elif name.endswith("_depl.csv"):
            depl_size = os.path.getsize(os.path.join(csv_dir, name))
    if men_size is None:
        raise RuntimeError(
            "File missing from EMC2: {}".format(os.path.join(csv_dir, "xxxxx_men.csv"))
        )
    if pers_size is None:
        raise RuntimeError(
            "File missing from EMC2: {}".format(os.path.join(csv_dir, "xxxxx_pers.csv"))
        )
    if depl_size is None:
        raise RuntimeError(
            "File missing from EMC2: {}".format(os.path.join(csv_dir, "xxxxx_depl.csv"))
        )

    # The file describing the zones is a shapefile or TAB file stored in `Doc/SIG/`.
    sig_dir = os.path.join(emc_dir, "Doc", "SIG")
    filelist = os.listdir(sig_dir)
    zf_size = 0
    for name in filelist:
        if "_ZF" in name:
            zf_size += os.path.getsize(os.path.join(sig_dir, name))
    if zf_size == 0:
        raise RuntimeError(
            "File missing from EMC2: {}".format(os.path.join(sig_dir, "xxxxx_ZF.[shp/TAB]"))
        )

    return [men_size, pers_size, depl_size, zf_size]
