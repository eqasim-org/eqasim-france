from synpp import ConfigurationContext, ExecuteContext
import matsim.runtime.eqasim as eqasim


def configure(context: ConfigurationContext):
    context.stage("data.hbefa.raw")

    context.config("output_path")
    context.config("cutter.name", "cutter")
    
    context.stage("matsim.simulation.cutter.full_run")

    eqasim.configure(context)
    context.stage("matsim.runtime.eqasim")


def execute(context: ExecuteContext):
    cutter_name = context.config("cutter.name")

    config_path = "%s/%s/%s_config.xml" % (
        context.config("output_path"),
        cutter_name,
        cutter_name
    )

    hbefa_folder = context.path("data.hbefa.raw")
    hbefa_cold_average, hbefa_hot_average, hbefa_cold_detailed, hbefa_hot_detailed = context.stage("data.hbefa.raw")

    args = [
        "--config-path", config_path,
        "--hbefa-cold-avg", "%s/%s" % (hbefa_folder, hbefa_cold_average),
        "--hbefa-hot-avg", "%s/%s" % (hbefa_folder, hbefa_hot_average),
        "--configurator-class", "org.eqasim.ile_de_france.IDFConfigurator",
    ]


    if hbefa_cold_detailed != "":
        args += [
            "--hbefa-cold-detailed", "%s/%s" % (hbefa_folder, hbefa_cold_detailed),
        ]
    
    
    if hbefa_hot_detailed != "":
        args += [
            "--hbefa-hot-detailed", "%s/%s" % (hbefa_folder, hbefa_hot_detailed),
        ]

    eqasim.run(
        context,
        "org.eqasim.core.components.emissions.RunComputeEmissionsEvents",
        args,
        cwd="%s/%s" % (context.config("output_path"), cutter_name),
    )
    
    return "output_emissions_events.xml.gz"