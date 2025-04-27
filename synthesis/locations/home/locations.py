import pandas as pd
import numpy as np
import geopandas as gpd

"""
This stage provides a list of home places that serve as potential locations for
home activities.
"""

def configure(context):
    context.stage("data.spatial.iris")
    if context.config("home_location_source", "addresses") == "tiles":
        context.stage("data.tiles.raw", alias = "location_source")
    else:
        context.stage("synthesis.locations.home.addresses", alias = "location_source")

def execute(context):
    # Find required IRIS
    df_iris = context.stage("data.spatial.iris")
    required_iris = set(df_iris["iris_id"].unique())
    
    # Load all addresses and add IRIS information
    df_addresses = context.stage("location_source")

    print("Imputing IRIS into addresses ...")
   
    df_addresses = gpd.sjoin(df_addresses,
        df_iris[["iris_id", "commune_id", "geometry"]], predicate = "within")
    del df_addresses["index_right"]
    
    df_addresses.loc[df_addresses["iris_id"].isna(), "iris_id"] = "unknown"
    df_addresses["iris_id"] = df_addresses["iris_id"].astype("category")

    df_addresses["fake"] = False

    # Add fake homes for IRIS without addresses
    missing_iris = required_iris - set(df_addresses["iris_id"].unique())

    if len(missing_iris) > 0:
        print("Adding homes at the centroid of %d/%d IRIS without BDTOPO observations" % (
            len(missing_iris), len(required_iris)))

        df_added = []
        for iris_id in sorted(missing_iris):
            centroid = df_iris[df_iris["iris_id"] == iris_id]["geometry"].centroid.iloc[0]

            df_added.append({
                "iris_id": iris_id, "geometry": centroid,
                "commune_id": iris_id[:5],
                "weight" : 1,
                "home_location_id": -1
            })

        df_added = gpd.GeoDataFrame(pd.DataFrame.from_records(df_added), crs = df_addresses.crs)
        df_added["fake"] = True

        df_addresses = pd.concat([df_addresses, df_added])

    # Add home identifier
    df_addresses["location_id"] = np.arange(len(df_addresses))
    df_addresses["location_id"] = "home_" + df_addresses["location_id"].astype(str)

    return df_addresses
