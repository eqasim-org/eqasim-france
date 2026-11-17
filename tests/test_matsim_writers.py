import gzip
import io
import itertools

import numpy as np
import pandas as pd
import pytest
import synpp

import matsim.scenario.facilities as facilities
import matsim.scenario.households as households
import matsim.scenario.population as population
import matsim.scenario.vehicles as vehicles
import matsim.writers as writers

"""
Checks that the vectorized MATSim writers produce exactly the same XML as the
former row-by-row writers, which are kept here as references.
"""

INPUT_STAGES = [
    "synthesis.population.enriched",
    "synthesis.population.activities",
    "synthesis.population.spatial.locations",
    "synthesis.population.trips",
    "synthesis.vehicles.vehicles",
    "synthesis.population.spatial.home.locations",
    "synthesis.population.spatial.primary.locations",
    "synthesis.locations.secondary",
]

@pytest.fixture(scope = "module")
def inputs(data_path, tmp_path_factory):
    config = dict(
        data_path = data_path, output_path = str(tmp_path_factory.mktemp("output")),
        regions = [10, 11], sampling_rate = 1.0, hts = "entd",
        random_seed = 1000, processes = 1,
        secondary_activities = dict(maximum_iterations = 10),
        maven_skip_tests = True
    )

    results = synpp.run([dict(descriptor = stage) for stage in INPUT_STAGES], config,
        working_directory = str(tmp_path_factory.mktemp("cache")))

    return dict(zip(INPUT_STAGES, results))

# Reference: the former row-by-row population writer

class backlog_iterator:
    def __init__(self, iterable, backlog = 1):
        self.iterable = iterable
        self.forward_log = []
        self.backward_log = [None] * (backlog + 1)

    def next(self):
        if len(self.forward_log) > 0:
            self.backward_log.append(self.forward_log[0])
            del self.forward_log[0]
        else:
            self.backward_log.append(next(self.iterable))

        del self.backward_log[0]
        return self.backward_log[-1]

    def previous(self):
        self.forward_log.insert(0, self.backward_log[-1])
        del self.backward_log[-1]
        self.backward_log.insert(0, None)
        return self.backward_log[-1]

    def current(self):
        return self.backlog[-1]

    def has_previous(self):
        return len(self.backward_log) > 1

    def has_next(self):
        if len(self.forward_log) > 0:
            return True

        try:
            self.forward_log.append(next(self.iterable))
            return True
        except StopIteration:
            return False


PERSON_FIELDS = [
    "person_id", "household_income", "car_availability", "bike_availability",
    "census_household_id", "census_person_id", "household_id",
    "has_license", "has_pt_subscription", "is_passenger",
    "hts_person_id", "hts_household_id",
    "age", "employed", "sex"
]

ACTIVITY_FIELDS = ["person_id", "start_time", "end_time", "purpose", "geometry", "location_id"]
TRIP_FIELDS = ["person_id", "mode", "departure_time", "travel_time"]
VEHICLE_FIELDS = ["owner_id", "vehicle_id", "mode"]

def reference_add_person(writer, person, activities, trips, vehicles):
    writer.start_person(person[PERSON_FIELDS.index("person_id")])

    writer.start_attributes()
    writer.add_attribute("householdId", "java.lang.Integer", person[PERSON_FIELDS.index("household_id")])
    writer.add_attribute("householdIncome", "java.lang.Double", person[PERSON_FIELDS.index("household_income")])

    writer.add_attribute("carAvailability", "java.lang.String", person[PERSON_FIELDS.index("car_availability")])
    writer.add_attribute("bikeAvailability", "java.lang.String", person[PERSON_FIELDS.index("bike_availability")])

    if person[PERSON_FIELDS.index("car_availability")] == "none":
        writer.add_attribute("carAvail", "java.lang.String", "never")

    if getattr(person, "use_motorcycle", -1) != -1:
        writer.add_attribute("useMotorcycle", "java.lang.Boolean", person.use_motorcycle)

    writer.add_attribute("censusHouseholdId", "java.lang.Long", person[PERSON_FIELDS.index("census_household_id")])
    writer.add_attribute("censusPersonId", "java.lang.Long", person[PERSON_FIELDS.index("census_person_id")])

    writer.add_attribute("htsHouseholdId", "java.lang.Long", person[PERSON_FIELDS.index("hts_household_id")])
    writer.add_attribute("htsPersonId", "java.lang.Long", person[PERSON_FIELDS.index("hts_person_id")])

    writer.add_attribute("hasPtSubscription", "java.lang.Boolean", person[PERSON_FIELDS.index("has_pt_subscription")])
    writer.add_attribute("hasLicense", "java.lang.String", writer.yes_no(person[PERSON_FIELDS.index("has_license")]))

    writer.add_attribute("isPassenger", "java.lang.Boolean", person[PERSON_FIELDS.index("is_passenger")])

    writer.add_attribute("age", "java.lang.Integer", person[PERSON_FIELDS.index("age")])
    writer.add_attribute("employed", "java.lang.String", person[PERSON_FIELDS.index("employed")])
    writer.add_attribute("sex", "java.lang.String", person[PERSON_FIELDS.index("sex")][0])

    writer.add_attribute("vehicles", "org.matsim.vehicles.PersonVehicles", "{{{content}}}".format(content = ",".join([
        "\"{mode}\":\"{id}\"".format(mode = v[VEHICLE_FIELDS.index("mode")], id = v[VEHICLE_FIELDS.index("vehicle_id")])
        for v in vehicles
    ])))

    writer.end_attributes()
    writer.start_plan(selected = True)

    for activity, trip in itertools.zip_longest(activities, trips):
        start_time = activity[ACTIVITY_FIELDS.index("start_time")]
        end_time = activity[ACTIVITY_FIELDS.index("end_time")]
        location_id = activity[ACTIVITY_FIELDS.index("location_id")]
        geometry = activity[ACTIVITY_FIELDS.index("geometry")]

        if activity[ACTIVITY_FIELDS.index("purpose")] == "home":
            location_id = "home_%s" % person[PERSON_FIELDS.index("household_id")]

        location = writer.location(geometry.x, geometry.y, None if location_id == -1 else location_id)

        writer.add_activity(
            type = activity[ACTIVITY_FIELDS.index("purpose")],
            location = location,
            start_time = None if np.isnan(start_time) else start_time,
            end_time = None if np.isnan(end_time) else end_time
        )

        if not trip is None:
            writer.add_leg(
                mode = trip[TRIP_FIELDS.index("mode")],
                departure_time = trip[TRIP_FIELDS.index("departure_time")],
                travel_time = trip[TRIP_FIELDS.index("travel_time")]
            )

    writer.end_plan()
    writer.end_person()

def reference_write(df_persons, df_activities, df_locations, df_trips, df_vehicles):
    df_persons = df_persons.sort_values(by = ["household_id", "person_id"])
    person_fields = PERSON_FIELDS + (["use_motorcycle"] if "use_motorcycle" in df_persons else [])
    df_persons = df_persons[person_fields]

    df_activities = df_activities.sort_values(by = ["person_id", "activity_index"])
    df_locations = df_locations[["person_id", "activity_index", "geometry", "location_id"]].sort_values(by = ["person_id", "activity_index"])
    df_activities = pd.merge(df_activities, df_locations, how = "left", on = ["person_id", "activity_index"])

    df_trips = df_trips.copy()
    df_trips["travel_time"] = df_trips["arrival_time"] - df_trips["departure_time"]

    df_vehicles = df_vehicles.sort_values(by = ["owner_id"])

    buffer = io.BytesIO()
    writer = writers.PopulationWriter(buffer)
    writer.start_population({ "coordinateReferenceSystem": df_locations.crs })

    activity_iterator = backlog_iterator(iter(df_activities[ACTIVITY_FIELDS].itertuples(index = False)))
    trip_iterator = backlog_iterator(iter(df_trips[TRIP_FIELDS].itertuples(index = False)))
    vehicle_iterator = backlog_iterator(iter(df_vehicles[VEHICLE_FIELDS].itertuples(index = False)))

    def collect(iterator, index, person_id):
        items = []

        while iterator.has_next():
            item = iterator.next()

            if not item[index] == person_id:
                iterator.previous()
                break

            items.append(item)

        return items

    for person in df_persons.itertuples(index = False):
        person_id = person[PERSON_FIELDS.index("person_id")]

        activities = collect(activity_iterator, ACTIVITY_FIELDS.index("person_id"), person_id)
        trips = collect(trip_iterator, TRIP_FIELDS.index("person_id"), person_id)
        vehicles = collect(vehicle_iterator, VEHICLE_FIELDS.index("owner_id"), person_id)

        assert len(activities) > 0
        assert len(trips) == len(activities) - 1

        reference_add_person(writer, person, activities, trips, vehicles)

    writer.end_population()
    return buffer.getvalue()

# Reference: the former row-by-row households, facilities and vehicles writers

HOUSEHOLD_FIELDS = ["household_id", "person_id", "household_income", "car_availability", "bike_availability", "census_household_id"]

def reference_write_households(df_persons):
    df_persons = df_persons.sort_values(by = ["household_id", "person_id"])[HOUSEHOLD_FIELDS]

    buffer = io.BytesIO()
    writer = writers.HouseholdsWriter(buffer)
    writer.start_households()

    def add_household(household, member_ids):
        writer.start_household(household[HOUSEHOLD_FIELDS.index("household_id")])
        writer.add_members(member_ids)

        writer.start_attributes()
        writer.add_attribute("carAvailability", "java.lang.String", household[HOUSEHOLD_FIELDS.index("car_availability")])
        writer.add_attribute("bikeAvailability", "java.lang.String", household[HOUSEHOLD_FIELDS.index("bike_availability")])
        writer.add_attribute("household_income", "java.lang.Double", household[HOUSEHOLD_FIELDS.index("household_income")])
        writer.add_attribute("censusId", "java.lang.Long", household[HOUSEHOLD_FIELDS.index("census_household_id")])
        writer.end_attributes()

        writer.end_household()

    current_members, current_household_id, current_household = [], None, None

    for item in df_persons.itertuples(index = False):
        if current_household_id != item[HOUSEHOLD_FIELDS.index("household_id")]:
            if not current_household_id is None:
                add_household(current_household, current_members)

            current_household = item
            current_household_id = item[HOUSEHOLD_FIELDS.index("household_id")]
            current_members = [item[HOUSEHOLD_FIELDS.index("person_id")]]
        else:
            current_members.append(item[HOUSEHOLD_FIELDS.index("person_id")])

    if not current_household_id is None:
        add_household(current_household, current_members)

    writer.end_households()
    return buffer.getvalue()

def reference_write_facilities(df_homes, df_work, df_education, df_secondary):
    buffer = io.BytesIO()
    writer = writers.FacilitiesWriter(buffer)
    writer.start_facilities({ "coordinateReferenceSystem": df_homes.crs })

    for item in df_homes[["household_id", "geometry"]].itertuples(index = False):
        writer.start_facility("home_%s" % item[0], item[1].x, item[1].y)
        writer.add_activity("home")
        writer.end_facility()

    df_work = df_work.drop_duplicates("location_id").copy()
    df_education = df_education.drop_duplicates("location_id").copy()
    df_work["is_work"] = True
    df_education["is_work"] = False

    df_locations = pd.concat([df_work, df_education])[["location_id", "geometry", "is_work"]]

    for item in df_locations.itertuples(index = False):
        writer.start_facility(str(item[0]), item[1].x, item[1].y)
        writer.add_activity("work" if item[2] else "education")
        writer.end_facility()

    fields = ["location_id", "geometry", "offers_leisure", "offers_shop", "offers_other"]

    for item in df_secondary[fields].itertuples(index = False):
        writer.start_facility(item[0], item[1].x, item[1].y)

        for purpose in ("shop", "leisure", "other"):
            if item[fields.index("offers_%s" % purpose)]:
                writer.add_activity(purpose)

        writer.end_facility()

    writer.end_facilities()
    return buffer.getvalue()

def reference_write_vehicles(df_vehicle_types, df_vehicles):
    buffer = io.BytesIO()
    writer = writers.VehiclesWriter(buffer)
    writer.start_vehicles()

    for type in df_vehicle_types.to_dict(orient = "records"):
        writer.add_type(
            type["type_id"], length = type["length"], width = type["width"], mode = type["mode"],
            attributes = { "CnossosCategory": type["cnossos_cat"] },
            engine_attributes = {
                "HbefaVehicleCategory": type["hbefa_cat"],
                "HbefaTechnology": type["hbefa_tech"],
                "HbefaSizeClass": type["hbefa_size"],
                "HbefaEmissionsConcept": type["hbefa_emission"]
            }
        )

    for vehicle in df_vehicles.to_dict(orient = "records"):
        writer.add_vehicle(vehicle["vehicle_id"], vehicle["type_id"], attributes = {
            "critair": vehicle["critair"], "technology": vehicle["technology"],
            "age": vehicle["age"], "euro": vehicle["euro"]
        })

    writer.end_vehicles()
    return buffer.getvalue()

# Tests

def _frames(inputs, drop_motorcycle = False):
    df_persons = inputs["synthesis.population.enriched"]

    if drop_motorcycle:
        df_persons = df_persons.drop(columns = ["use_motorcycle"], errors = "ignore")

    return (
        df_persons,
        inputs["synthesis.population.activities"],
        inputs["synthesis.population.spatial.locations"],
        inputs["synthesis.population.trips"],
        inputs["synthesis.vehicles.vehicles"][1],
    )

@pytest.mark.parametrize("workers,chunk_size", [(1, population.CHUNK_SIZE), (3, 7), (2, 1)])
@pytest.mark.parametrize("drop_motorcycle", [False, True])
def test_population_writer_matches_reference(inputs, workers, chunk_size, drop_motorcycle):
    frames = _frames(inputs, drop_motorcycle)
    expected = reference_write(*frames)

    persons, activities, trips, activity_counts = population.prepare(*frames)

    output = io.BytesIO()
    population.write(output, persons, activities, trips, activity_counts, frames[2].crs,
        workers = workers, chunk_size = chunk_size)

    actual = gzip.decompress(output.getvalue())

    assert ("useMotorcycle" in actual.decode()) != drop_motorcycle
    assert actual == expected

CHUNKING = [(1, None), (3, 7), (2, 1)] # workers, chunk size (None: default)

def _write(module, *arguments, workers, chunk_size):
    output = io.BytesIO()
    options = dict(workers = workers)
    if chunk_size is not None: options["chunk_size"] = chunk_size
    module.write(output, *arguments, **options)
    return gzip.decompress(output.getvalue())

@pytest.mark.parametrize("workers,chunk_size", CHUNKING)
def test_households_writer_matches_reference(inputs, workers, chunk_size):
    df_persons = inputs["synthesis.population.enriched"]

    expected = reference_write_households(df_persons)
    actual = _write(households, households.prepare(df_persons), workers = workers, chunk_size = chunk_size)

    assert actual == expected

@pytest.mark.parametrize("workers,chunk_size", CHUNKING)
@pytest.mark.parametrize("random_offers", [False, True])
def test_facilities_writer_matches_reference(inputs, workers, chunk_size, random_offers):
    df_homes = inputs["synthesis.population.spatial.home.locations"]
    df_work, df_education = inputs["synthesis.population.spatial.primary.locations"]
    df_secondary = inputs["synthesis.locations.secondary"]

    if random_offers: # the fixture lacks some combinations (e.g. shop and leisure)
        df_secondary = df_secondary.copy()
        random = np.random.default_rng(0)

        for purpose in ("shop", "leisure", "other"):
            df_secondary["offers_%s" % purpose] = random.random(len(df_secondary)) < 0.5

    expected = reference_write_facilities(df_homes, df_work, df_education, df_secondary)
    actual = _write(facilities, facilities.prepare(df_homes, df_work, df_education, df_secondary), df_homes.crs,
        workers = workers, chunk_size = chunk_size)

    assert actual == expected

@pytest.mark.parametrize("workers,chunk_size", CHUNKING)
def test_vehicles_writer_matches_reference(inputs, workers, chunk_size):
    df_vehicle_types, df_vehicles = inputs["synthesis.vehicles.vehicles"]

    expected = reference_write_vehicles(df_vehicle_types, df_vehicles)
    actual = _write(vehicles, df_vehicle_types, vehicles.prepare(df_vehicles), workers = workers, chunk_size = chunk_size)

    assert actual == expected

def test_format_float_f():
    random = np.random.default_rng(0)

    values = np.concatenate([
        random.uniform(0, 1.3e6, 100_000), # Lambert 93 range
        random.uniform(-1e3, 1e3, 10_000),
        np.round(random.uniform(0, 1e6, 10_000), 2),
        np.arange(10_000) + 0.5e-6, # around rounding ties
        np.arange(10_000) + 2.5e-6,
        np.arange(10_000) * 1e-7,
        [0.0, -0.0, -1e-9, 1e-9, 0.4999995e-6, 1.5e-6, 2**52, 2**53 + 0.5, 1e20, -1e20,
         np.nan, np.inf, -np.inf],
    ])

    assert writers.format_float_f(values).to_list() == ["%f" % value for value in values]

def test_format_python_float():
    random = np.random.default_rng(0)

    values = np.concatenate([
        random.uniform(0, 1e5, 10_000),
        random.lognormal(0, 20, 10_000),
        [0.0, -0.0, 1.0, 1e-4, 9.99e-5, 1e15, 1e16, 1.5e17, 123456789.0, np.nan, np.inf, -np.inf],
    ])

    assert writers.format_python_float(values).to_list() == [str(value) for value in values]

def test_format_time():
    writer = writers.XmlWriter(None)
    values = np.concatenate([np.arange(0, 200000, 7.3), [0.0, 59.999, 3600.0, 86399.0, 360000.0, np.nan]])

    assert writers.format_time(values).to_list() == [writer.time(value) for value in values]

def test_vehicle_order_matches_pandas_sort():
    # The vehicles attribute keeps the order of pandas' (unstable) sort_values on the owner
    random = np.random.default_rng(0)
    owners = random.integers(0, 1000, 100_000)

    expected = pd.DataFrame({ "owner_id": owners }).sort_values(by = ["owner_id"]).index.to_numpy()
    assert np.array_equal(np.argsort(owners, kind = "quicksort"), expected)
