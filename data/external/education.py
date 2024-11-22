import shapely.geometry as geo
import numpy as np
import pandas as pd
import geopandas as gpd

def configure(context):
    context.stage("data.bpe.cleaned")
    context.stage("data.spatial.municipalities")

    context.config("data_path")
    context.config("education_file", "education/education_addresses.geojson")

def execute(context):
    df_locations = context.stage("data.bpe.cleaned")[[
         "activity_type", "education_type", "commune_id","weight", "geometry"
    ]]

    df_locations = df_locations[df_locations["activity_type"] == "education"]
    df_locations = df_locations[["activity_type","education_type", "commune_id", "geometry"]].copy()
    df_locations["fake"] = False    

    df_zones = context.stage("data.spatial.municipalities")    
    required_communes = set(df_zones["commune_id"].unique())      


    df_education = gpd.read_file("{}/{}".format(context.config("data_path"), context.config("education_file")))[["education_type", "commune_id","weight", "geometry"]]
    df_education["fake"] = False
    df_education = df_education.to_crs("2154")
    df_education["activity_type"] = "education"
    list_type = set(df_education["education_type"].unique())
    df_locations = pd.concat([df_locations[~(df_locations["education_type"].str.startswith(tuple(list_type)))],df_education[df_education["commune_id"].isin(required_communes)]])

    return df_locations
