from synpp import ConfigurationContext, ExecuteContext

import matsim.runtime.eqasim as eqasim

def configure(context: ConfigurationContext):
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")

    context.stage("matsim.scenario.supply.processed")

    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")


def execute(context: ExecuteContext):
    # Prepare input paths
    network_path = "%s/%s" % (
        context.path("matsim.scenario.supply.processed"),
        context.stage("matsim.scenario.supply.processed")["network_path"]
    )

    schedule_path = "%s/%s" % (
        context.path("matsim.scenario.supply.processed"),
        context.stage("matsim.scenario.supply.processed")["schedule_path"]
    )

    crs = "EPSG:2154"

    eqasim.run(context, "org.eqasim.core.tools.ExportNetworkToGeopackage", [
        "--network-path", network_path,
        "--output-path", "%s/%snetwork.gpkg" % (
            context.config("output_path"),
            context.config("output_prefix")
        ),
        "--crs", crs,
    ])

    eqasim.run(context, "org.eqasim.core.tools.ExportTransitStopsToShapefile", [
        "--schedule-path", schedule_path,
        "--output-path", "%s/%stransit_stops.shp" % (
            context.config("output_path"),
            context.config("output_prefix")
        ),
        "--crs", crs,
    ])

    eqasim.run(context, "org.eqasim.core.tools.ExportTransitLinesToShapefile", [
        "--schedule-path", schedule_path,
        "--network-path", network_path,
        "--output-path", "%s/%stransit_lines.shp" % (
            context.config("output_path"),
            context.config("output_prefix")
        ),
        "--crs", crs,
    ])

