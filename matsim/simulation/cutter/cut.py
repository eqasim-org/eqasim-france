import os
import matsim.runtime.eqasim as eqasim

from synpp import ConfigurationContext, ExecuteContext

def configure(context: ConfigurationContext):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

    context.config("cutter_name", "cutter")

    context.stage("data.cutter.geometry")
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")

    context.stage("matsim.simulation.full_run")


def execute(context: ExecuteContext):
    config_path = "%s/%sconfig.xml" % (
        context.config("output_path"),
        context.config("output_prefix"),
    )

    cutter_name = context.config("cutter_name")

    gpd_cutter = context.stage("data.cutter.geometry")
    
    geometry_file = "%s/%s.shp" % (context.path(), cutter_name)
    
    gpd_cutter.to_file(
        geometry_file
    )

    initial_simulation_path = "%s/simulation_output" % context.config("output_path")
    cutter_simulation_path = "%s/%s" % (
        context.config("output_path"),
        cutter_name,
    )
    eqasim.run(
        context,
        "org.eqasim.core.scenario.cutter.RunScenarioCutter",
        [
            "--config-path", config_path,
            "--output-path", cutter_simulation_path,
            "--extent-path", geometry_file,
            "--config:plans.inputPlansFile", "%s/output_plans.xml.gz" % initial_simulation_path,
            "--prefix", cutter_name + "_"
        ],
        cwd=initial_simulation_path,
    )

    assert os.path.exists(
        "%s/%s_config.xml" % (cutter_simulation_path, cutter_name)
    )
