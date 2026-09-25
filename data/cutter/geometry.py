import os
import geopandas as gpd

from synpp import ConfigurationContext, ExecuteContext, ValidateContext


def configure(context: ConfigurationContext):
    context.config("data_path")
    context.config("cutter.path", "cutter")
    context.config("cutter.file", "cutter.geojson")
    context.config("crs", "EPSG:2154")


def execute(context: ExecuteContext):
    cutter_path = "%s/%s/%s" % (
        context.config("data_path"),
        context.config("cutter.path"),
        context.config("cutter.file"),
    )

    # Load the shapefile using geopandas
    gdf = gpd.read_file(cutter_path)

    # Check if the geometry column exists and is valid
    if "geometry" not in gdf.columns or gdf["geometry"].is_empty.any():
        raise ValueError("The file does not contain a valid geometry column.")

    return gdf.to_crs(context.config("crs"))


def validate(context: ValidateContext):
    cutter_path = "%s/%s" % (context.config("data_path"), context.config("cutter.path"))

    # Check if the cutter path exists
    if not os.path.exists(cutter_path):
        raise FileNotFoundError(f"Cutter path does not exist: {cutter_path}")
