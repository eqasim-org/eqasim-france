from synpp import ConfigurationContext, ExecuteContext

import os
import os.path
import shapely.geometry as sgeo
import glob
import osmium
import geopandas as gpd

def configure(context: ConfigurationContext):
    context.stage("data.cutter.geometry")
    context.config("data_path")
    context.config("osm_path", "osm_idf")


def execute(context: ExecuteContext):

    source_paths = get_source_paths("{}/{}".format(context.config("data_path"), context.config("osm_path")))
    
    # Prepare bounding area
    df_area: gpd.GeoDataFrame = context.stage("data.cutter.geometry")
    area = df_area.to_crs("EPSG:4326")["geometry"].values[0]

    # Read identifiers that are relevant
    tracker = osmium.IdTracker()

    for source_path in source_paths:
        processor = osmium.FileProcessor(source_path).with_filter(
            osmium.filter.KeyFilter("building")).with_locations().with_filter(
            osmium.filter.GeoInterfaceFilter())
        
        for item in context.progress(processor, label = "Reading {} ...".format(source_path.split("/")[-1])):
            geometry = sgeo.shape(item.__geo_interface__["geometry"])

            if area.intersects(geometry):
                tracker.add_way(item.id) # add the way itself
                tracker.add_references(item) # add the referenced nodes
    
    # Read all files again in parallel and write out the relevant items
    processors = [
        osmium.FileProcessor(source_path).with_filter(tracker.id_filter()).with_locations()
        for source_path in source_paths
    ]

    output_path = "{}/output.osm.pbf".format(context.path())
    with osmium.SimpleWriter(output_path) as writer:
        for items in context.progress(osmium.zip_processors(*processors), label = "Writing ..."):
            for item_index, item in enumerate(items):
                if item:
                    writer.add(item)
                    break # already written, skip duplicate

    return "output.osm.pbf"

def get_source_paths(base_path):
    osm_paths = sorted(list(glob.glob("{}/*.osm.pbf".format(base_path))))
    osm_paths += sorted(list(glob.glob("{}/*.osm.xml".format(base_path))))

    if len(osm_paths) == 0:
        raise RuntimeError("Did not find any OSM data (.osm.pbf) in {}".format(base_path))
    
    return osm_paths

def validate(context):
    input_files = get_source_paths("{}/{}".format(context.config("data_path"), context.config("osm_path")))
    total_size = 0

    for path in input_files:
        total_size += os.path.getsize(path)

    return total_size
