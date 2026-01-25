from synpp import ConfigurationContext, ExecuteContext
import matsim.runtime.eqasim as eqasim


def configure(context: ConfigurationContext):
    context.config("output_path")
    context.config("cutter.name", "cutter")

    context.config("emissions_polutants", "PM,CO,NOx")
    context.config("emissions_time_bin_size", 3600)
    
    context.stage("matsim.simulation.emissions.events")

    context.stage("matsim.runtime.eqasim")


def execute(context: ExecuteContext):
    cutter_name = context.config("cutter.name")

    config_path = "%s/%s/%s_config.xml" % (
        context.config("output_path"),
        cutter_name,
        cutter_name
    )

    eqasim.run(context, "org.eqasim.core.components.emissions.RunExportEmissionsNetwork", [
        "--config-path", config_path,
        "--pollutants", context.config("emissions_polutants"),
        "--time-bin-size", str(context.config("emissions_time_bin_size")),
        "--configurator-class", "org.eqasim.ile_de_france.IDFConfigurator",
    ], cwd="%s/%s" % (context.config("output_path"), cutter_name))

    return "emissions_network.shp"