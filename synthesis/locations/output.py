import pandas as pd
import geopandas as gpd

def configure(context):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")
    context.config("output_formats", ["csv", "gpkg"])

    context.stage("synthesis.locations.home.locations")
    context.stage("synthesis.locations.work")
    context.stage("synthesis.locations.education")
    context.stage("synthesis.locations.secondary")

def execute(context):

    output_formats = context.config("output_formats")

    gdf_homes: gpd.GeoDataFrame = context.stage("synthesis.locations.home.locations")
    gdf_work: gpd.GeoDataFrame = context.stage("synthesis.locations.work")
    gdf_education: gpd.GeoDataFrame = context.stage("synthesis.locations.education")
    gdf_secondary: gpd.GeoDataFrame = context.stage("synthesis.locations.secondary")

    if "geojson" in output_formats:

        gdf_homes.astype({ "iris_id": str }).to_file("%s/%sall_potential_housing.geojson" % (
            context.config("output_path"), context.config("output_prefix")
        ))

        gdf_work.astype({ "commune_id": str }).to_file("%s/%sall_potential_work.geojson" % (
            context.config("output_path"), context.config("output_prefix")
        ))

        gdf_education.astype({
            "education_type": str,
            "commune_id": str
        }).to_file("%s/%sall_potential_education.geojson" % (
            context.config("output_path"), context.config("output_prefix")
        ))

        gdf_secondary.astype({
            "activity_type": str,
            "commune_id": str
        }).to_file("%s/%sall_potential_secondary.geojson" % (
            context.config("output_path"), context.config("output_prefix")
        ))

    if "gpkg" in output_formats:

        gdf_homes.to_file("%s/%sall_potential_housing.gpkg" % (
            context.config("output_path"), context.config("output_prefix")
        ), driver = "GPKG", layer = "all_potential_housing")

        gdf_work.to_file("%s/%sall_potential_work.gpkg" % (
            context.config("output_path"), context.config("output_prefix")
        ), driver = "GPKG", layer = "all_potential_work")

        gdf_education.to_file("%s/%sall_potential_education.gpkg" % (
            context.config("output_path"), context.config("output_prefix")
        ), driver = "GPKG", layer = "all_potential_education")

        gdf_secondary.to_file("%s/%sall_potential_secondary.gpkg" % (
            context.config("output_path"), context.config("output_prefix")
        ), driver = "GPKG", layer = "all_potential_secondary")

    if "parquet" in output_formats:

        gdf_homes.to_parquet("%s/%sall_potential_housing.parquet" % (
            context.config("output_path"), context.config("output_prefix")
        ))

        gdf_work.to_parquet("%s/%sall_potential_work.parquet" % (
            context.config("output_path"), context.config("output_prefix")
        ))

        gdf_education.to_parquet("%s/%sall_potential_education.parquet" % (
            context.config("output_path"), context.config("output_prefix")
        ))

        gdf_secondary.to_parquet("%s/%sall_potential_secondary.parquet" % (
            context.config("output_path"), context.config("output_prefix")
        ))