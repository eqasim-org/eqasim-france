import shutil
import os.path

import matsim.runtime.eqasim as eqasim


def configure(context):
    context.stage("matsim.simulation.prepare")

    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")


def execute(context):
    config_path = "%s/%s" % (
        context.path("matsim.simulation.prepare"),
        context.stage("matsim.simulation.prepare"),
    )

    # Run routing
    eqasim.run(
        context,
        "org.eqasim.ile_de_france.RunSimulation",
        [
            "--config-path",
            config_path,
            "--config:controler.lastIteration",
            str(1),
            "--config:controler.writeEventsInterval",
            str(1),
            "--config:controler.writePlansInterval",
            str(1),
        ],
    )
    assert os.path.exists("%s/simulation_output/output_events.xml.gz" % context.path())
