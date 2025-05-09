import os
import geopandas as gpd

from synpp import ConfigurationContext, ExecuteContext, ValidateContext


def configure(context: ConfigurationContext):
    context.config("data_path")
    context.config("cutter_path", "cutter")
    context.config("cutter_file", "cutter.geojson")


def execute(context: ExecuteContext):
    cutter_path = "%s/%s/%s" % (
        context.config("data_path"),
        context.config("cutter_path"),
        context.config("cutter_file"),
    )

    # Load the shapefile using geopandas
    gdf = gpd.read_file(cutter_path)

    # Check if the geometry column exists and is valid
    if "geometry" not in gdf.columns or gdf["geometry"].is_empty.any():
        raise ValueError("The file does not contain a valid geometry column.")

    return gdf


def validate(context: ValidateContext):
    cutter_path = "%s/%s" % (context.config("data_path"), context.config("cutter_path"))

    # Check if the cutter path exists
    if not os.path.exists(cutter_path):
        raise FileNotFoundError(f"Cutter path does not exist: {cutter_path}")
