import os.path

import matsim.runtime.pt2matsim as pt2matsim

def configure(context):
    pt2matsim.configure(context)
    context.stage("matsim.runtime.pt2matsim")
    
    context.stage("data.gtfs.cleaned")
    context.config("crs", "EPSG:2154")

    context.config("gtfs_date", "dayWithMostServices")

def execute(context):
    gtfs_path = "{}/gtfs.zip".format(context.path("data.gtfs.cleaned"))

    pt2matsim.run(context, "org.matsim.pt2matsim.run.Gtfs2TransitScheduleWithParameters", [
        "--input-path", gtfs_path,
        "--day", context.config("gtfs_date"), 
        "--crs", context.config("crs"),
        "--output-schedule-path", "{}/transit_schedule.xml.gz".format(context.path()),
        "--output-vehicles-path", "{}/transit_vehicles.xml.gz".format(context.path()),
        "--write-crs", "true"
    ])

    assert(os.path.exists("{}/transit_schedule.xml.gz".format(context.path())))
    assert(os.path.exists("{}/transit_vehicles.xml.gz".format(context.path())))

    return dict(
        schedule_path = "transit_schedule.xml.gz",
        vehicles_path = "transit_vehicles.xml.gz"
    )
