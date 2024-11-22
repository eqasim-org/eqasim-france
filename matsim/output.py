import shutil

def configure(context):
    if context.config("run_matsim", True):
        # allow disabling performing one run of the simulation
        context.stage("matsim.simulation.run")
    
    context.stage("matsim.simulation.prepare")
    context.stage("matsim.runtime.eqasim")

    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")
    context.config("write_jar", True)
    need_osm = context.config("export_detailed_network", False)
    if need_osm:
        context.stage("matsim.scenario.supply.osm")
    

    context.stage("documentation.meta_output")

def execute(context):
    config_path = "%s/%s" % (
        context.path("matsim.simulation.prepare"),
        context.stage("matsim.simulation.prepare")
    )

    file_names = [
        "%shouseholds.xml.gz" % context.config("output_prefix"),
        "%spopulation.xml.gz" % context.config("output_prefix"),
        "%svehicles.xml.gz" % context.config("output_prefix"),
        "%sfacilities.xml.gz" % context.config("output_prefix"),
        "%snetwork.xml.gz" % context.config("output_prefix"),
        "%stransit_schedule.xml.gz" % context.config("output_prefix"),
        "%stransit_vehicles.xml.gz" % context.config("output_prefix"),
        "%sconfig.xml" % context.config("output_prefix")
    ]

    for name in file_names:
        shutil.copy(
            "%s/%s" % (context.path("matsim.simulation.prepare"), name),
            "%s/%s" % (context.config("output_path"), name)
        )

    if context.config("export_detailed_network"):
        shutil.copy(
            "%s/%s" % (context.path("matsim.scenario.supply.osm"), "detailed_network.csv"),
            "%s/%s" % (context.config("output_path"), "%sdetailed_network.csv" % context.config("output_prefix"))
        )
    
    if context.config("write_jar"):
        shutil.copy(
            "%s/%s" % (context.path("matsim.runtime.eqasim"), context.stage("matsim.runtime.eqasim")),
            "%s/%srun.jar" % (context.config("output_path"), context.config("output_prefix"))
        )
