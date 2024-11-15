import io, gzip
import itertools

import numpy as np
import pandas as pd

import matsim.writers as writers
from matsim.writers import backlog_iterator


def configure(context):
    context.stage("synthesis.population.enriched")

    context.stage("synthesis.population.activities")
    context.stage("synthesis.population.spatial.locations")

    context.stage("synthesis.population.trips")
    context.stage("synthesis.vehicles.vehicles")


PERSON_FIELDS = [
    "person_id",
    "household_income",
    "car_availability",
    "bike_availability",
    "census_household_id",
    "census_person_id",
    "household_id",
    "has_license",
    "has_pt_subscription",
    "is_passenger",
    "hts_id",
    "hts_household_id",
    "age",
    "employed",
    "sex",
]

ACTIVITY_FIELDS = [
    "person_id",
    "start_time",
    "end_time",
    "purpose",
    "geometry",
    "location_id",
]

TRIP_FIELDS = ["person_id", "mode", "departure_time", "travel_time"]

VEHICLE_FIELDS = ["owner_id", "vehicle_id", "mode"]


def add_person(writer, person, activities, trips, vehicles):
    writer.start_person(person[PERSON_FIELDS.index("person_id")])

    writer.start_attributes()
    writer.add_attribute(
        "householdId", "java.lang.Integer", person[PERSON_FIELDS.index("household_id")]
    )
    writer.add_attribute(
        "householdIncome",
        "java.lang.Double",
        person[PERSON_FIELDS.index("household_income")],
    )

    writer.add_attribute(
        "carAvailability",
        "java.lang.String",
        person[PERSON_FIELDS.index("car_availability")],
    )
    writer.add_attribute(
        "bikeAvailability",
        "java.lang.String",
        person[PERSON_FIELDS.index("bike_availability")],
    )

    writer.add_attribute(
        "censusHouseholdId",
        "java.lang.Long",
        person[PERSON_FIELDS.index("census_household_id")],
    )
    writer.add_attribute(
        "censusPersonId",
        "java.lang.Long",
        person[PERSON_FIELDS.index("census_person_id")],
    )

    writer.add_attribute(
        "htsHouseholdId",
        "java.lang.Long",
        person[PERSON_FIELDS.index("hts_household_id")],
    )
    writer.add_attribute(
        "htsPersonId", "java.lang.Long", person[PERSON_FIELDS.index("hts_id")]
    )

    writer.add_attribute(
        "hasPtSubscription",
        "java.lang.Boolean",
        person[PERSON_FIELDS.index("has_pt_subscription")],
    )
    writer.add_attribute(
        "hasLicense",
        "java.lang.String",
        writer.yes_no(person[PERSON_FIELDS.index("has_license")]),
    )

    writer.add_attribute(
        "isPassenger", "java.lang.Boolean", person[PERSON_FIELDS.index("is_passenger")]
    )

    writer.add_attribute("age", "java.lang.Integer", person[PERSON_FIELDS.index("age")])
    writer.add_attribute(
        "employed", "java.lang.String", person[PERSON_FIELDS.index("employed")]
    )
    writer.add_attribute(
        "sex", "java.lang.String", person[PERSON_FIELDS.index("sex")][0]
    )

    writer.add_attribute(
        "vehicles",
        "org.matsim.vehicles.PersonVehicles",
        "{{{content}}}".format(
            content=",".join(
                [
                    '"{mode}":"{id}"'.format(
                        mode=v[VEHICLE_FIELDS.index("mode")],
                        id=v[VEHICLE_FIELDS.index("vehicle_id")],
                    )
                    for v in vehicles
                ]
            )
        ),
    )

    writer.end_attributes()

    writer.start_plan(selected=True)

    for activity, trip in itertools.zip_longest(activities, trips):
        start_time = activity[ACTIVITY_FIELDS.index("start_time")]
        end_time = activity[ACTIVITY_FIELDS.index("end_time")]
        location_id = activity[ACTIVITY_FIELDS.index("location_id")]
        geometry = activity[ACTIVITY_FIELDS.index("geometry")]

        if activity[ACTIVITY_FIELDS.index("purpose")] == "home":
            location_id = "home_%s" % person[PERSON_FIELDS.index("household_id")]

        location = writer.location(
            geometry.x, geometry.y, None if location_id == -1 else location_id
        )

        writer.add_activity(
            type=activity[ACTIVITY_FIELDS.index("purpose")],
            location=location,
            start_time=None if np.isnan(start_time) else start_time,
            end_time=None if np.isnan(end_time) else end_time,
        )

        if not trip is None:
            writer.add_leg(
                mode=trip[TRIP_FIELDS.index("mode")],
                departure_time=trip[TRIP_FIELDS.index("departure_time")],
                travel_time=trip[TRIP_FIELDS.index("travel_time")],
            )

    writer.end_plan()
    writer.end_person()


def execute(context):
    output_path = "%s/population.xml.gz" % context.path()

    df_persons = context.stage("synthesis.population.enriched")
    df_persons = df_persons.sort_values(by=["household_id", "person_id"])
    df_persons = df_persons[PERSON_FIELDS]

    df_activities = context.stage("synthesis.population.activities").sort_values(
        by=["person_id", "activity_index"]
    )
    df_locations = context.stage("synthesis.population.spatial.locations")[
        ["person_id", "activity_index", "geometry", "location_id"]
    ].sort_values(by=["person_id", "activity_index"])

    df_activities = pd.merge(
        df_activities, df_locations, how="left", on=["person_id", "activity_index"]
    )
    # df_activities["location_id"] = df_activities["location_id"].fillna(-1).astype(int)

    df_trips = context.stage("synthesis.population.trips")
    df_trips["travel_time"] = df_trips["arrival_time"] - df_trips["departure_time"]

    df_vehicles = context.stage("synthesis.vehicles.vehicles")[1]
    df_vehicles = df_vehicles.sort_values(by=["owner_id"])

    with gzip.open(output_path, "wb+") as writer:
        with io.BufferedWriter(writer, buffer_size=2 * 1024**3) as writer:
            writer = writers.PopulationWriter(writer)
            writer.start_population()

            activity_iterator = backlog_iterator(
                iter(df_activities[ACTIVITY_FIELDS].itertuples(index=False))
            )
            trip_iterator = backlog_iterator(
                iter(df_trips[TRIP_FIELDS].itertuples(index=False))
            )
            vehicle_iterator = backlog_iterator(
                iter(df_vehicles[VEHICLE_FIELDS].itertuples(index=False))
            )

            with context.progress(
                total=len(df_persons), label="Writing population ..."
            ) as progress:
                for person in df_persons.itertuples(index=False):
                    person_id = person[PERSON_FIELDS.index("person_id")]

                    activities = []
                    trips = []
                    vehicles = []

                    # Track all activities for person
                    while activity_iterator.has_next():
                        activity = activity_iterator.next()

                        if (
                            not activity[ACTIVITY_FIELDS.index("person_id")]
                            == person_id
                        ):
                            activity_iterator.previous()
                            break
                        else:
                            activities.append(activity)

                    assert len(activities) > 0

                    # Track all trips for person
                    while trip_iterator.has_next():
                        trip = trip_iterator.next()

                        if not trip[TRIP_FIELDS.index("person_id")] == person_id:
                            trip_iterator.previous()
                            break
                        else:
                            trips.append(trip)

                    assert len(trips) == len(activities) - 1

                    # Track all vehicles for person
                    while vehicle_iterator.has_next():
                        vehicle = vehicle_iterator.next()

                        if not vehicle[VEHICLE_FIELDS.index("owner_id")] == person_id:
                            vehicle_iterator.previous()
                            break
                        else:
                            vehicles.append(vehicle)

                    add_person(writer, person, activities, trips, vehicles)
                    progress.update()

            writer.end_population()

    return "population.xml.gz"
