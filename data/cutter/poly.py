import os
import geopandas as gpd

from synpp import ConfigurationContext, ExecuteContext


def configure(context: ConfigurationContext):
    context.config("data_path")
    context.config("cutter_path", "cutter")
    context.config("cutter_file", "cutter.geojson")


def execute(context: ExecuteContext):

    gdf = context.stage("data.cutter.geometry")

    poly_file = "cutter.poly"
    poly_path = "%s/%s" % (context.path(), poly_file)

    write_poly(gdf, poly_path)

    return poly_file

# taken from https://gist.github.com/sebhoerl/9a19135ffeeaede9f0abd4cdfedea3bc
def write_poly(gdf: gpd.GeoDataFrame, path: str, geometry_column: str = "geometry"):
    gdf = gdf.to_crs("EPSG:4326")

    gdf["aggregate"] = 0
    area: gpd.GeoDataFrame = gdf.dissolve(by="aggregate")[geometry_column].values[0]

    if not hasattr(area, "exterior"):
        print("Selected area is not connected -> Using convex hull.")
        area = area.convex_hull

    data = []
    data.append("polyfile")
    data.append("polygon")

    for coordinate in area.exterior.coords:
        data.append("    %e    %e" % coordinate)

    data.append("END")
    data.append("END")

    with open(path, "w+") as f:
        f.write("\n".join(data))

