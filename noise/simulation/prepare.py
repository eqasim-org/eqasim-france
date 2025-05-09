from synpp import ConfigurationContext, ExecuteContext
import os
import shutil
from pathlib import Path


def configure(context: ConfigurationContext):
    context.stage("noise.simulation.osm")

    context.config("output_path")
    context.config("cutter_name", "cutter")

    context.config("sampling_rate")

def execute(context: ExecuteContext):
    
    sampling_rate = context.config("sampling_rate")

    osm_path = Path("%s/%s" % (context.path("noise.simulation.osm"), context.stage("noise.simulation.osm")))

    simulation_path = Path("%s/%s/simulation_output" % (context.config("output_path"), context.config("cutter_name")))

    noisemodelling_path = simulation_path / "noisemodelling"
    osm_destination = noisemodelling_path / "map.osm.pbf"

    if not osm_destination.parent.exists():
        os.makedirs(osm_destination.parent)

    shutil.copy(osm_path.as_posix(), osm_destination.as_posix())

    results_path = noisemodelling_path / "results"
    inputs_path = noisemodelling_path / "inputs"
    db_name = "file:///%s/noisemodelling" % noisemodelling_path.as_posix()

    if not results_path.exists():
        os.makedirs(results_path)

    if not inputs_path.exists():
        os.makedirs(inputs_path)

    properties_path = noisemodelling_path / "noisemodelling.properties"

    with open(properties_path, 'w') as properties_file:
        properties_file.write(f"DB_NAME={db_name}\n")
        properties_file.write(f"OSM_FILE_PATH={osm_destination.as_posix()}\n")
        properties_file.write(f"MATSIM_DIR={simulation_path.as_posix()}\n")
        properties_file.write(f"INPUTS_DIR={inputs_path.as_posix()}\n")
        properties_file.write(f"RESULTS_DIR={results_path.as_posix()}\n")
        properties_file.write("SRID=2154\n")
        properties_file.write(f"POPULATION_FACTOR={sampling_rate}\n")
        properties_file.write("DO_IMPORT_OSM=True\n")
        properties_file.write("DO_RUN_NOISEMODELLING=True\n")
        properties_file.write("DO_EXPORT_BUILDINGS=True\n")
        properties_file.write("DO_EXPORT_RESULTS=True\n")

    return properties_path
