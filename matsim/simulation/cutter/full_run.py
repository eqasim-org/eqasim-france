import os
import matsim.runtime.eqasim as eqasim
from synpp import ConfigurationContext, ExecuteContext


def configure(context: ConfigurationContext):
    context.config("output_path")

    context.config("cutter_name", "cutter")

    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")

    context.stage("matsim.simulation.cutter.cut")

def execute(context: ExecuteContext):

    cutter_name = context.config("cutter_name")

    config_path = "%s/%s/%s_config.xml" % (
        context.config("output_path"),
        cutter_name,
        cutter_name
    )

    eqasim.run(
        context,
        "org.eqasim.ile_de_france.RunSimulation",
        [
            "--config-path",
            config_path,
            "--config:planCalcScore.writeExperiencedPlans",
            "true",
        ],
        cwd="%s/%s" % (context.config("output_path"), cutter_name),
    )

    assert os.path.exists(
        "%s/%s/simulation_output/output_events.xml.gz" % (context.config("output_path"), cutter_name)
    )
