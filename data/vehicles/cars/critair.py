import numpy as np
import pandas as pd
import mock, os, glob
from openpyxl.reader import excel
import zipfile

"""
This stage loads the raw data of the specified vehicle fleet data
https://www.statistiques.developpement-durable.gouv.fr/donnees-sur-le-parc-automobile-francais-au-1er-janvier-2021
"""

def configure(context):
    context.config("data_path")
    context.config("vehicles_path", "vehicles")
    context.config("vehicles_year", 2021)
    context.stage("data.spatial.codes")

def execute(context):
    df_codes = context.stage("data.spatial.codes")

    # the downloaded excel files meta-data are actually have a badly formatted ISO datetime
    # https://foss.heptapod.net/openpyxl/openpyxl/-/issues/1659 
    with mock.patch.object(excel.ExcelReader, 'read_properties', lambda self: None):
        year = str(context.config("vehicles_year"))
        
        with zipfile.ZipFile("{}/{}/{}".format(context.config("data_path"), context.config("vehicles_path"), "parc_vp_communes.zip")) as archive:
            with archive.open("Parc_VP_Communes_{}.xlsx".format(year)) as f:
                df_municipalities = pd.read_excel(f)

        with zipfile.ZipFile("{}/{}/{}".format(context.config("data_path"), context.config("vehicles_path"), "parc_vp_regions.zip")) as archive:
            with archive.open("Parc_VP_Regions_{}.xlsx".format(year)) as f:
                df_regions = pd.read_excel(f)
    
    df_municipalities["region_id"] = df_municipalities["Code région"].astype("category")
    df_municipalities["departement_id"] = df_municipalities["Code départment"].astype("category")
    df_municipalities["commune_id"] = df_municipalities["Code commune"].astype("category")

    df_regions["region_id"] = df_regions["Code région"].astype("category")

    requested_departements = set(df_codes["departement_id"].unique())
    requested_regions = set(df_codes["region_id"].astype(str).unique())

    if len(requested_departements) > 0:
        df_municipalities = df_municipalities[df_municipalities["departement_id"].isin(requested_departements)]

    if len(requested_regions) > 0:
        df_regions = df_regions[df_regions["region_id"].isin(requested_regions)]

    df_municipalities["region_id"] = df_municipalities["region_id"].cat.remove_unused_categories()
    df_municipalities["departement_id"] = df_municipalities["departement_id"].cat.remove_unused_categories()
    df_municipalities["commune_id"] = df_municipalities["commune_id"].cat.remove_unused_categories()

    df_regions["region_id"] = df_regions["region_id"].cat.remove_unused_categories()

    df_municipalities["critair"] = df_municipalities["Vignette Crit'air"]
    df_municipalities["technology"] = df_municipalities["Energie"]

    df_regions["critair"] = df_regions["Vignette crit'air"]
    df_regions["technology"] = df_regions["Energie"]

    count_column_name = "Parc au 01/01/%s" % context.config("vehicles_year")
    age_column_name = "Age au 01/01/%s" % context.config("vehicles_year")

    df_municipalities["fleet"] = df_municipalities[count_column_name]
    df_regions["fleet"] = df_regions[count_column_name]
    df_regions["age"] = df_regions[age_column_name]

    df_vehicle_fleet_counts = df_municipalities.groupby(["region_id", "commune_id", "critair","technology"])["fleet"].sum().reset_index().dropna()
    df_vehicle_age_counts = df_regions.groupby(["region_id", "critair", "technology", "age"])["fleet"].sum().reset_index().dropna()

    return df_vehicle_fleet_counts, df_vehicle_age_counts

def validate(context):
    municipalities_path = "{}/{}/{}".format(context.config("data_path"), context.config("vehicles_path"), "parc_vp_communes.zip")
    regions_path = "{}/{}/{}".format(context.config("data_path"), context.config("vehicles_path"), "parc_vp_regions.zip")

    if not os.path.exists(municipalities_path):
        raise RuntimeError("Municipalities vehicle data is not available at {}".format(municipalities_path))
    
    if not os.path.exists(regions_path):
        raise RuntimeError("Regions vehicle data is not available at {}".format(regions_path))

    return os.path.getsize(municipalities_path) + os.path.getsize(regions_path)
