import pandas as pd
import numpy as np
import geopandas as gpd
import numpy as np

"""
This stage assigns adresses from BAN to residential buildings from BD TOPO.

The match is based on distance from building shape perimeter in every direction 
(buffer expressed as meters). The distance value is set to 5 meters by default 
and in most case is between 1 to 20 meters in the data.

The output is one or several rows per building depending on the match (one or 
many adresses). For every building the housing count is distributed to the matching 
adresses. For instance, the assigned addresses of a building with 10 housing units
and two addresses will have a weight of 5.

If no adresses matches a building, its centroid is taken as the unique address.
"""

def configure(context):
    context.stage("data.bdtopo.raw")
    
    context.config("home_address_buffer", 5.0)

    context.config("home_location_weight", "housing")
    if context.config("home_location_source", "addresses") == "addresses":
        context.stage("data.ban.raw")

def execute(context):
    # Load buildings
    df_buildings = context.stage("data.bdtopo.raw")
    print("Number of buildings:", + len(df_buildings))

    if context.config("home_location_source") == "buildings":
        df_addresses = pd.DataFrame({
            "building_id": [], "housing": [], "geometry": []
        })

    else: # addresses
        # Load addresses
        df_addresses = context.stage("data.ban.raw")[["geometry"]].copy()
        print("Number of addresses:", + len(df_addresses))

        # Buffer buildings to capture adresses in their vicinity
        df_buffer = df_buildings[["building_id", "housing", "geometry"]].copy()
        df_buffer["geometry"] = df_buffer.buffer(context.config("home_address_buffer"))

        # Find close-by addresses
        df_addresses = gpd.sjoin(df_addresses, df_buffer, predicate = "within")[[
            "building_id", "housing", "geometry"]]
    
    # Create missing addresses by using centroids
    df_missing = df_buildings[~df_buildings["building_id"].isin(df_addresses["building_id"])].copy()
    df_missing["geometry"] = df_missing["geometry"].centroid
    df_missing = df_missing[["building_id", "housing", "geometry"]]

    # Put together matched and missing addresses
    df_addresses = pd.concat([df_addresses, df_missing])
    df_addresses = gpd.GeoDataFrame(df_addresses, crs = df_buildings.crs).rename(columns={"building_id":"home_location_id"})

    # Obtain weights for all addresses
    if context.config("home_location_weight") == "housing":
        df_count = df_addresses.groupby("home_location_id").size().reset_index(name = "count")
        df_addresses = pd.merge(df_addresses, df_count, on = "home_location_id")
        df_addresses["weight"] = df_addresses["housing"] / df_addresses["count"]
    else:
        df_addresses["weight"] = 1.0
    
    return df_addresses[["home_location_id", "weight", "geometry"]]

def validate(context):
    assert context.config("home_location_source") in ("addresses", "buildings","tiles")
    assert context.config("home_location_weight") in ("uniform", "housing")
