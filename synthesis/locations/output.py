import pandas as pd
import geopandas as gpd

def configure(context):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

    context.stage("synthesis.locations.home.locations")
    context.stage("synthesis.locations.work")
    context.stage("synthesis.locations.education")
    context.stage("synthesis.locations.secondary")

def execute(context):

    gdf_homes: gpd.GeoDataFrame = context.stage("synthesis.locations.home.locations")
    gdf_work: gpd.GeoDataFrame = context.stage("synthesis.locations.work")
    gdf_education: gpd.GeoDataFrame = context.stage("synthesis.locations.education")
    gdf_secondary: gpd.GeoDataFrame = context.stage("synthesis.locations.secondary")

    gdf_homes = gdf_homes.astype({
        "iris_id": str,
    })
    gdf_homes.to_file("%s/%sall_potential_housing.geojson" % (
        context.config("output_path"), context.config("output_prefix")
    ))

    gdf_work = gdf_work.astype({
        "commune_id": str
    })
    gdf_work.to_file("%s/%sall_potential_work.geojson" % (
        context.config("output_path"), context.config("output_prefix")
    ))
    
    gdf_education = gdf_education.astype({
        "education_type": str,
        "commune_id": str
    })
    gdf_education.to_file("%s/%sall_potential_education.geojson" % (
        context.config("output_path"), context.config("output_prefix")
    ))

    gdf_secondary = gdf_secondary.astype({
        "activity_type": str,
        "commune_id": str
    })
    gdf_secondary.to_file("%s/%sall_potential_secondary.geojson" % (
        context.config("output_path"), context.config("output_prefix")
    ))