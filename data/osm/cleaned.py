import data.osm.osmosis
import os, os.path, gzip
import shapely.geometry as geo
import glob

"""
This file reads the OSM data in PBF format specified by the "osm_path"
and "data_path" configuration options. The data is read from
"data_path/osm_path". Note that you can define a list of input files separated
by ";" in the "osm_path" option. These OSM files will be merged, for instance,
if you want to merge the old Languedoc and Midi-Pyrénées regional snapshots
from Geofabrik to create a continuous file for the new Occitanie region.

This stage furthermore filters the file such that only highway elmenets and
railway elements of the OSM data remain. This makes it easier for the downstream
MATSim converter to work with the data.

Additionally, the stage cuts the OSM data to the requested region of the pipeline.
"""

def configure(context):
    context.config("data_path")
    context.config("osm_path", "osm_idf")

    context.config("osm_highways", "*")
    context.config("osm_railways", "*")

    context.stage("data.osm.osmosis")
    context.stage("data.spatial.municipalities")

def write_poly(df, path, geometry_column = "geometry"):
    df = df.to_crs("EPSG:4326")

    df["aggregate"] = 0
    area = df.dissolve(by = "aggregate")[geometry_column].values[0]

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

def execute(context):
    input_files = get_input_files("{}/{}".format(context.config("data_path"), context.config("osm_path")))
    
    # Prepare bounding area
    df_area = context.stage("data.spatial.municipalities")
    write_poly(df_area, "%s/boundary.poly" % context.path())

    # Filter input files for quicker processing
    for index, path in enumerate(input_files):
        print("Filtering %s ..." % path.split("/")[-1])
        print("Depending on the amount of OSM data, this may take quite some time!")

        mode = "pbf" if path.endswith("pbf") else "xml"

        highway_tags = context.config("osm_highways")
        railway_tags = context.config("osm_railways")

        absolute_path = os.path.abspath(path)

        data.osm.osmosis.run(context, [
            "--read-%s" % mode, absolute_path,
            "--tag-filter", "accept-ways", "highway=%s" % highway_tags, "railway=%s" % railway_tags,
            "--bounding-polygon", "file=%s/boundary.poly" % context.path(), "completeWays=yes",
            "--write-pbf", "filtered_%d.osm.pbf" % index
        ])

    # Merge filtered files if there are multiple ones
    print("Merging and compressing OSM data...")

    command = []
    for index in range(len(input_files)):
        command += ["--read-pbf", "filtered_%d.osm.pbf" % index]

    for index in range(len(input_files) - 1):
        command += ["--merge"]

    command += ["--write-xml", "compressionMethod=gzip", "output.osm.gz"]

    data.osm.osmosis.run(context, command)

    # Remove temporary files
    for index, path in enumerate(input_files):
        print("Removing temporary file for %s ..." % path)
        os.remove("%s/filtered_%d.osm.pbf" % (context.path(), index))

    return "output.osm.gz"

def get_input_files(base_path):
    osm_paths = sorted(list(glob.glob("{}/*.osm.pbf".format(base_path))))
    osm_paths += sorted(list(glob.glob("{}/*.osm.xml".format(base_path))))

    if len(osm_paths) == 0:
        raise RuntimeError("Did not find any OSM data (.osm.pbf) in {}".format(base_path))
    
    return osm_paths

def validate(context):
    input_files = get_input_files("{}/{}".format(context.config("data_path"), context.config("osm_path")))
    total_size = 0

    for path in input_files:
        total_size += os.path.getsize(path)

    return total_size
