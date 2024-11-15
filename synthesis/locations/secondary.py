import shapely.geometry as geo
import numpy as np
import pandas as pd
import geopandas as gpd


def configure(context):
    context.stage("data.bpe.cleaned")
    context.stage("data.spatial.municipalities")


def execute(context):
    df_locations = context.stage("data.bpe.cleaned")[
        ["enterprise_id", "activity_type", "commune_id", "geometry"]
    ].copy()
    df_locations["destination_id"] = np.arange(len(df_locations))

    # Attach attributes for activity types
    df_locations["offers_leisure"] = df_locations["activity_type"] == "leisure"
    df_locations["offers_shop"] = df_locations["activity_type"] == "shop"
    df_locations["offers_other"] = ~(
        df_locations["offers_leisure"] | df_locations["offers_shop"]
    )

    # Define new IDs
    df_locations["location_id"] = np.arange(len(df_locations))
    df_locations["location_id"] = "sec_" + df_locations["location_id"].astype(str)

    return df_locations
