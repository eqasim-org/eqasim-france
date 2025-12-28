import os.path

import matsim.runtime.pt2matsim as pt2matsim

def configure(context):
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.pt2matsim")
    context.stage("data.gtfs.cleaned")
    context.stage("data.spatial.iris")

    context.config("gtfs_date", "dayWithMostServices")

def execute(context):
    gtfs_path = "{}/gtfs.zip".format(context.path("data.gtfs.cleaned"))
    crs = context.stage("data.spatial.iris").crs

    pt2matsim.run(context, "org.matsim.pt2matsim.run.Gtfs2TransitScheduleWithParameters", [
        "--input-path", gtfs_path,
        "--day", context.config("gtfs_date"), 
        "--crs", crs, "--write-crs", "true",
        "--output-schedule-path", "{}/transit_schedule.xml.gz".format(context.path()),
        "--output-vehicles-path", "{}/transit_vehicles.xml.gz".format(context.path())
    ])

    assert(os.path.exists("{}/transit_schedule.xml.gz".format(context.path())))
    assert(os.path.exists("{}/transit_vehicles.xml.gz".format(context.path())))

    return dict(
        schedule_path = "transit_schedule.xml.gz",
        vehicles_path = "transit_vehicles.xml.gz"
    )
