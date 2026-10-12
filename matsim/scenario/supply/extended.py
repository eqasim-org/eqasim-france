import os.path
import numpy as np
import shutil

import matsim.runtime.eqasim as eqasim

def configure(context):
    eqasim.configure(context)
    context.stage("matsim.runtime.eqasim")

    if context.config("matsim.schedule_days", 1) == "auto":
        context.stage("synthesis.population.trips")

    context.stage("matsim.scenario.supply.processed")
    context.stage("matsim.scenario.supply.gtfs")

def execute(context):
    days = context.config("matsim.schedule_days")
    hours = 0

    if days == "auto":
        df_trips = context.stage("synthesis.population.trips")

        end_time = df_trips["arrival_time"].values
        end_time = np.max(end_time[np.isfinite(end_time)])

        days = max(1, int(np.floor(end_time / 3600.0 / 24.0)))
        hours = max(0, int(np.ceil((end_time - days * 3600.0 * 24.0) / 3600.0)))
        hours += 5 # fixed

    # make sure this is an integer
    days = int(days)

    schedule_path = "{}/{}".format(
        context.path("matsim.scenario.supply.processed"),
        context.stage("matsim.scenario.supply.processed")["schedule_path"]
    )

    vehicles_path = "{}/{}".format(
        context.path("matsim.scenario.supply.gtfs"),
        context.stage("matsim.scenario.supply.gtfs")["vehicles_path"]
    )

    if days == 1 and hours == 0:
        shutil.copy(schedule_path, "{}/transit_schedule.xml.gz".format(context.path()))
        shutil.copy(vehicles_path, "{}/transit_vehicles.xml.gz".format(context.path()))
    else:
        eqasim.run(context, "org.eqasim.core.tools.schedule.RunExtendSchedule", [
            "--input-schedule-path", schedule_path,
            "--input-vehicles-path", vehicles_path,
            "--output-schedule-path", "{}/transit_schedule.xml.gz".format(context.cache_path),
            "--output-vehicles-path", "{}/transit_vehicles.xml.gz".format(context.cache_path),
            "--days", str(days), "--hours", str(hours)
        ])

    assert(os.path.exists("{}/transit_schedule.xml.gz".format(context.path())))
    assert(os.path.exists("{}/transit_vehicles.xml.gz".format(context.path())))

    return dict(
        schedule = "transit_schedule.xml.gz",
        vehicles = "transit_vehicles.xml.gz",
    )
