import os.path

import matsim.runtime.pt2matsim as pt2matsim

def configure(context):
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.pt2matsim")
    context.stage("data.gtfs.cleaned")
    context.stage("data.spatial.iris")

    context.config("gtfs_date", "dayWithMostServices")

def execute(context):
    gtfs_path = "%s/output" % context.path("data.gtfs.cleaned")
    crs = context.stage("data.spatial.iris").crs

    pt2matsim.run(context, "org.matsim.pt2matsim.run.Gtfs2TransitSchedule", [
        gtfs_path,
        context.config("gtfs_date"), crs,
        "%s/transit_schedule.xml.gz" % context.path(),
        "%s/transit_vehicles.xml.gz" % context.path()
    ])

    assert(os.path.exists("%s/transit_schedule.xml.gz" % context.path()))
    assert(os.path.exists("%s/transit_vehicles.xml.gz" % context.path()))

    return dict(
        schedule_path = "transit_schedule.xml.gz",
        vehicles_path = "transit_vehicles.xml.gz"
    )
