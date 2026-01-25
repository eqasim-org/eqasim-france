import os
import matsim.runtime.eqasim as eqasim
import geopandas as gpd
from synpp import ConfigurationContext, ExecuteContext

def configure(context: ConfigurationContext):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

    context.config("cutter.name", "cutter")
    context.config("cutter.after_full_simulation", True)

    context.stage("data.cutter.geometry")
    context.stage("matsim.runtime.eqasim")

    context.stage("matsim.output")

    if context.config("cutter.after_full_simulation"):
        context.stage("matsim.simulation.full_run")



def execute(context: ExecuteContext):
    output_path = context.config("output_path")

    config_path = "%s/%sconfig.xml" % (
        output_path,
        context.config("output_prefix"),
    )

    cutter_name = context.config("cutter.name")

    gpd_cutter: gpd.GeoDataFrame = context.stage("data.cutter.geometry")
    
    geometry_file = "%s/%s.shp" % (context.path(), cutter_name)
    
    gpd_cutter.to_file(
        geometry_file
    )

    cutter_simulation_path = "%s/%s" % (
        output_path,
        cutter_name,
    )
    args = [
        "--config-path", config_path,
        "--output-path", cutter_simulation_path,
        "--extent-path", geometry_file,
        "--prefix", cutter_name + "_"
    ]

    if context.config("cutter.after_full_simulation"):
        args += [
            "--config:plans.inputPlansFile", "%s/simulation_output/output_plans.xml.gz" % output_path,
        ]
    
    eqasim.run(
        context,
        "org.eqasim.core.scenario.cutter.RunScenarioCutter",
        args,
        cwd=output_path,
    )

    assert os.path.exists(
        "%s/%s_config.xml" % (cutter_simulation_path, cutter_name)
    )
