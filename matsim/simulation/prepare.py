import shutil
import os.path

import matsim.runtime.eqasim as eqasim

def configure(context):
    context.config("mode_choice", False)
    
    context.stage("matsim.scenario.population")
    context.stage("matsim.scenario.households")
    context.stage("matsim.scenario.vehicles")

    context.stage("matsim.scenario.facilities")
    context.stage("matsim.scenario.supply.processed")
    context.stage("matsim.scenario.supply.gtfs")

    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.eqasim")

    context.stage("data.spatial.departments")
    context.stage("data.spatial.codes")

    context.config("sampling_rate")
    context.config("processes")
    context.config("random_seed")

    context.config("output_prefix", "ile_de_france_")

def execute(context):
    # Prepare input files
    facilities_path = "%s/%s" % (
        context.path("matsim.scenario.facilities"),
        context.stage("matsim.scenario.facilities")
    )

    population_path = "%s/%s" % (
        context.path("matsim.scenario.population"),
        context.stage("matsim.scenario.population")
    )

    network_path = "%s/%s" % (
        context.path("matsim.scenario.supply.processed"),
        context.stage("matsim.scenario.supply.processed")["network_path"]
    )

    eqasim.run(context, "org.eqasim.core.scenario.preparation.RunPreparation", [
        "--input-facilities-path", facilities_path,
        "--output-facilities-path", "%sfacilities.xml.gz" % context.config("output_prefix"),
        "--input-population-path", population_path,
        "--output-population-path", "prepared_population.xml.gz",
        "--input-network-path", network_path,
        "--output-network-path", "%snetwork.xml.gz" % context.config("output_prefix"),
        "--threads", context.config("processes")
    ])

    assert os.path.exists("%s/%sfacilities.xml.gz" % (context.path(), context.config("output_prefix")))
    assert os.path.exists("%s/prepared_population.xml.gz" % context.path())
    assert os.path.exists("%s/%snetwork.xml.gz" % (context.path(), context.config("output_prefix")))

    # Copy remaining input files
    households_path = "%s/%s" % (
        context.path("matsim.scenario.households"),
        context.stage("matsim.scenario.households")
    )
    shutil.copy(households_path, "%s/%shouseholds.xml.gz" % (context.cache_path, context.config("output_prefix")))

    transit_schedule_path = "%s/%s" % (
        context.path("matsim.scenario.supply.processed"),
        context.stage("matsim.scenario.supply.processed")["schedule_path"]
    )
    shutil.copy(transit_schedule_path, "%s/%stransit_schedule.xml.gz" % (context.cache_path, context.config("output_prefix")))

    transit_vehicles_path = "%s/%s" % (
        context.path("matsim.scenario.supply.gtfs"),
        context.stage("matsim.scenario.supply.gtfs")["vehicles_path"]
    )
    shutil.copy(transit_vehicles_path, "%s/%stransit_vehicles.xml.gz" % (context.cache_path, context.config("output_prefix")))

    vehicles_path = "%s/%s" % (
        context.path("matsim.scenario.vehicles"),
        context.stage("matsim.scenario.vehicles")
    )
    shutil.copy(vehicles_path, "%s/%svehicles.xml.gz" % (context.cache_path, context.config("output_prefix")))

    # Generate base configuration
    eqasim.run(context, "org.eqasim.core.scenario.config.RunGenerateConfig", [
        "--sample-size", context.config("sampling_rate"),
        "--threads", context.config("processes"),
        "--prefix", context.config("output_prefix"),
        "--random-seed", context.config("random_seed"),
        "--output-path", "generic_config.xml"
    ])
    assert os.path.exists("%s/generic_config.xml" % context.path())

    # Adapt config for Île-de-France
    eqasim.run(context, "org.eqasim.ile_de_france.scenario.RunAdaptConfig", [
        "--input-path", "generic_config.xml",
        "--output-path", "%sconfig.xml" % context.config("output_prefix"),
        "--prefix", context.config("output_prefix")
    ])
    assert os.path.exists("%s/%sconfig.xml" % (context.path(), context.config("output_prefix")))

    # Add urban attributes to population and network
    # (but only if Paris is included in the scenario!)
    df_codes = context.stage("data.spatial.codes")

    if "75" in df_codes["departement_id"].unique().astype(str):
        df_shape = context.stage("data.spatial.departments")[["departement_id", "geometry"]].rename(
            columns = dict(departement_id = "id")
        )
        df_shape["id"] = df_shape["id"].astype(str)

        if "75" in df_shape["id"].unique():
            df_shape.to_file("%s/departments.shp" % context.path())

            eqasim.run(context, "org.eqasim.core.scenario.spatial.RunImputeSpatialAttribute", [
                "--input-population-path", "prepared_population.xml.gz",
                "--output-population-path", "prepared_population.xml.gz",
                "--input-schedule-path", "{}transit_schedule.xml.gz".format(context.config("output_prefix")),
                "--output-schedule-path", "{}transit_schedule.xml.gz".format(context.config("output_prefix")),
                "--shape-path", "departments.shp",
                "--shape-attribute", "id",
                "--shape-value", "75",
                "--attribute", "isParis"
            ])
    
    # Optionally, perform mode choice
    if context.config("mode_choice"):
        eqasim.run(context, "org.eqasim.core.standalone_mode_choice.RunStandaloneModeChoice", [
            "--config-path", "%sconfig.xml" % context.config("output_prefix"),
            "--config:standaloneModeChoice.outputDirectory", "mode_choice",
            "--config:global.numberOfThreads", context.config("processes"),
            "--write-output-csv-trips", "true",
            "--skip-scenario-check", "true",
            "--config:plans.inputPlansFile", "prepared_population.xml.gz",
            "--eqasim-configurator-class", "org.eqasim.ile_de_france.IDFConfigurator",
            "--mode-choice-configurator-class", "org.eqasim.ile_de_france.IDFStandaloneModeChoiceConfigurator"
        ])

        assert os.path.exists("%s/mode_choice/output_plans.xml.gz" % context.path())
        assert os.path.exists("%s/mode_choice/output_trips.csv" % context.path())
        assert os.path.exists("%s/mode_choice/output_pt_legs.csv" % context.path())

        shutil.copy("%s/mode_choice/output_plans.xml.gz" % context.path(),
                    "%s/%spopulation.xml.gz" % (context.path(), context.config("output_prefix")))
    else:
        # Route population
        eqasim.run(context, "org.eqasim.core.scenario.routing.RunPopulationRouting", [
            "--config-path", "%sconfig.xml" % context.config("output_prefix"),
            "--output-path", "%spopulation.xml.gz" % context.config("output_prefix"),
            "--threads", context.config("processes"),
            "--config:plans.inputPlansFile", "prepared_population.xml.gz"
        ])

    assert os.path.exists("%s/%spopulation.xml.gz" % (context.path(), context.config("output_prefix")))

    # Validate scenario
    eqasim.run(context, "org.eqasim.core.scenario.validation.RunScenarioValidator", [
        "--config-path", "%sconfig.xml" % context.config("output_prefix")
    ])

    # Cleanup
    os.remove("%s/prepared_population.xml.gz" % context.path())

    return "%sconfig.xml" % context.config("output_prefix")
