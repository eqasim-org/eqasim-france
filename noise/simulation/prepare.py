from synpp import ConfigurationContext, ExecuteContext
import os
import shutil
from pathlib import Path


def configure(context: ConfigurationContext):
    context.stage("matsim.simulation.cutter.full_run")

    context.stage("noise.simulation.detailed_network")
    context.stage("noise.simulation.osm")
    
    context.config("output_path")
    context.config("cutter.name", "cutter")

    context.config("sampling_rate")

def execute(context: ExecuteContext):
    
    sampling_rate = context.config("sampling_rate")
    simulation_path = Path("%s/%s/simulation_output" % (context.config("output_path"), context.config("cutter.name")))

    # Place the osm file in the noisemodelling folder
    osm_path = Path("%s/%s" % (context.path("noise.simulation.osm"), context.stage("noise.simulation.osm")))

    noisemodelling_path = simulation_path / "noisemodelling"
    osm_destination = noisemodelling_path / "map.osm.pbf"

    if not osm_destination.parent.exists():
        os.makedirs(osm_destination.parent)

    shutil.copy(osm_path.as_posix(), osm_destination.as_posix())

    # place the detailed network in the simulation folder
    detailed_network_path = context.stage("noise.simulation.detailed_network")
    detailed_network_destination = simulation_path / "detailed_network.csv"

    if not detailed_network_destination.parent.exists():
        os.makedirs(detailed_network_destination.parent)

    shutil.copy(detailed_network_path, detailed_network_destination)

    # setup the rest of the folders
    results_path = noisemodelling_path / "results"
    inputs_path = noisemodelling_path / "inputs"
    db_name = "file:///%s/noisemodelling" % noisemodelling_path.as_posix()

    if not results_path.exists():
        os.makedirs(results_path)

    if not inputs_path.exists():
        os.makedirs(inputs_path)


    # create the noisemodelling config file
    properties_path = noisemodelling_path / "noisemodelling.properties"

    with open(properties_path, 'w') as properties_file:
        properties_file.write(f"DB_NAME={db_name}\n")
        properties_file.write(f"OSM_FILE_PATH={osm_destination.as_posix()}\n")
        properties_file.write(f"MATSIM_DIR={simulation_path.as_posix()}\n")
        properties_file.write(f"INPUTS_DIR={inputs_path.as_posix()}\n")
        properties_file.write(f"RESULTS_DIR={results_path.as_posix()}\n")
        properties_file.write("SRID=2154\n")
        properties_file.write(f"POPULATION_FACTOR={sampling_rate}\n")

    return properties_path
