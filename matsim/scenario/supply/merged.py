import matsim.scenario.supply.schedule_merge as schedule_merge

"""
Optionally merges the transit routes of the processed schedule that only differ
in their timing (see matsim.scenario.supply.schedule_merge).

This is a separate stage so that changing the tolerance does not run pt2matsim
again. Stages that use the transit schedule call configure_schedule in their
configure step and get_schedule_path in their execute step, so that this stage
only runs if pt_schedule_merge_tolerance is positive.
"""

def configure_tolerance(context):
    return float(context.config("pt_schedule_merge_tolerance", 0))

def get_tolerance(context):
    return float(context.config("pt_schedule_merge_tolerance"))

def configure(context):
    context.stage("matsim.scenario.supply.processed")
    configure_tolerance(context)

def execute(context):
    tolerance = get_tolerance(context)

    input_path = "%s/%s" % (
        context.path("matsim.scenario.supply.processed"),
        context.stage("matsim.scenario.supply.processed")["schedule_path"]
    )

    statistics = schedule_merge.merge_schedule_file(input_path, "%s/schedule.xml.gz" % context.path(), tolerance)

    print("Merged %d transit routes (tolerance %.0f s): %d routes and %d route stops left, %d departures shifted by up to %.0f s" % (
        statistics["merged_routes"], tolerance, statistics["routes"], statistics["route_stops"],
        statistics["shifted_departures"], statistics["maximum_shift"]))

    return "schedule.xml.gz"

def configure_schedule(context):
    """ Declares the stages providing the transit schedule """
    context.stage("matsim.scenario.supply.processed")

    if configure_tolerance(context) > 0:
        context.stage("matsim.scenario.supply.merged")

def get_schedule_path(context):
    """ Returns the path to the (merged) transit schedule """
    if get_tolerance(context) > 0:
        return "%s/%s" % (
            context.path("matsim.scenario.supply.merged"),
            context.stage("matsim.scenario.supply.merged")
        )

    return "%s/%s" % (
        context.path("matsim.scenario.supply.processed"),
        context.stage("matsim.scenario.supply.processed")["schedule_path"]
    )
