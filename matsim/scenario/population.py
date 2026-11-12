import collections
import gzip
import io
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import polars as pl
import shapely

import matsim.writers as writers

"""
Writes the MATSim population (population.xml.gz).

The XML text is built column-wise with polars for chunks of persons instead of
row by row. Chunks are formatted and compressed in a thread pool (polars and
zlib release the GIL); each chunk becomes its own gzip member, and the members
are concatenated, which is a valid gzip stream for Python, zcat and Java's
GZIPInputStream. The decompressed content is identical to the former
row-by-row writer.
"""

CHUNK_SIZE = 20_000 # persons per chunk / gzip member
COMPRESS_LEVEL = 9

def configure(context):
    context.stage("synthesis.population.enriched")

    context.stage("synthesis.population.activities")
    context.stage("synthesis.population.spatial.locations")

    context.stage("synthesis.population.trips")
    context.stage("synthesis.vehicles.vehicles")

    context.config("processes")

# Formatting helpers, all equivalent to the Python formatting used before

def format_float_f(values):
    """ Vectorized, exact equivalent of "%f" % value

    Values are scaled to micro-units and rounded in float64. Where the scaled
    value is too close to a rounding tie for that to be exact (or is out of the
    exactly representable range or not finite), Python's formatting is used.
    """
    values = np.asarray(values, dtype = np.float64)
    negative = np.signbit(values)

    scaled = np.abs(values) * 1e6

    with np.errstate(invalid = "ignore"):
        fraction = scaled - np.floor(scaled)
        safe = np.isfinite(scaled) & (scaled < 2.0**52) & (
            np.abs(fraction - 0.5) > 4.0 * np.spacing(scaled))

    micro = np.where(safe, np.rint(scaled), 0.0).astype(np.int64)

    result = pl.select(pl.concat_str([
        pl.when(pl.lit(negative)).then(pl.lit("-")).otherwise(pl.lit("")),
        pl.lit(micro // 1_000_000).cast(pl.String), pl.lit("."),
        pl.lit(micro % 1_000_000).cast(pl.String).str.zfill(6),
    ])).to_series()

    unsafe = np.flatnonzero(~safe)

    if len(unsafe) > 0:
        result = result.scatter(unsafe, ["%f" % value for value in values[unsafe]])

    return result

def format_time(values):
    """ Vectorized writers.XmlWriter.time, NaN gives null """
    values = np.asarray(values, dtype = np.float64)
    missing = np.isnan(values)
    seconds = np.where(missing, 0, values).astype(np.int64) # truncation like int()

    result = pl.select(pl.concat_str([
        pl.lit(seconds // 3600).cast(pl.String).str.zfill(2), pl.lit(":"),
        pl.lit((seconds % 3600) // 60).cast(pl.String).str.zfill(2), pl.lit(":"),
        pl.lit(seconds % 60).cast(pl.String).str.zfill(2),
    ])).to_series()

    if missing.any():
        result = result.scatter(np.flatnonzero(missing), None)

    return result

def format_python_float(values):
    """ Vectorized str(float) """
    values = np.asarray(values, dtype = np.float64)
    result = pl.Series(values).cast(pl.String)

    # polars and Python agree on the shortest round-trip digits, but not on
    # exponent notation and special values: use Python there
    with np.errstate(invalid = "ignore"):
        special = ~np.isfinite(values) | (np.abs(values) >= 1e16) | ((values != 0) & (np.abs(values) < 1e-4))

    index = np.flatnonzero(special)

    if len(index) > 0:
        result = result.scatter(index, [str(value) for value in values[index]])

    return result

def _choose(mask, if_true, if_false):
    """ String series with if_true where mask is set, if_false elsewhere """
    return pl.select(pl.when(pl.lit(np.asarray(mask, dtype = bool)))
        .then(pl.lit(if_true)).otherwise(pl.lit(if_false))).to_series()

def format_python_bool(values):
    """ Vectorized str(value) for a boolean column """
    values = pd.Series(values)

    if values.dtype == bool:
        return _choose(values.to_numpy(), "True", "False")

    return pl.Series([str(value) for value in values]) # e.g. object columns with NaN

def _attribute(name, java_class, value):
    return [
        pl.lit('      <attribute name="%s" class="%s">' % (name, java_class)),
        value, pl.lit("</attribute>\n")
    ]

def _from_pandas(df, columns):
    """ Converts columns of a pandas frame to polars (Arrow strings and categories stay as they are) """
    return pl.from_pandas(pd.DataFrame(df[columns]), include_index = False)

def _as_string(column):
    """ Equivalent of str(value) for string / categorical columns, as written before """
    return pl.col(column).cast(pl.String).fill_null("nan")

# Preparation and writing

def prepare(df_persons, df_activities, df_locations, df_trips, df_vehicles):
    """ Brings the inputs into output order as polars frames """

    # Persons in output order
    persons = _from_pandas(df_persons, [
        "person_id", "household_id", "car_availability", "bike_availability",
        "census_household_id", "census_person_id", "hts_household_id", "hts_person_id", "age", "sex"
    ]).with_columns(
        household_income = format_python_float(df_persons["household_income"].to_numpy()),
        has_pt_subscription = format_python_bool(df_persons["has_pt_subscription"]),
        # truthiness of the (object) column, NaN counts as "yes"
        has_license = _choose(df_persons["has_license"].to_numpy().astype(bool), "yes", "no"),
        is_passenger = format_python_bool(df_persons["is_passenger"]),
        employed = format_python_bool(df_persons["employed"]),
    )

    if "use_motorcycle" in df_persons:
        persons = persons.with_columns(use_motorcycle = format_python_bool(df_persons["use_motorcycle"]))

    persons = persons.with_columns(
        _as_string("car_availability"), _as_string("bike_availability"),
        _as_string("sex").str.slice(0, 1),
    ).sort(["household_id", "person_id"]).with_row_index("p")

    # Vehicles attribute per person. The vehicle order is the one of the former
    # pandas sort_values(by = "owner_id"), an unstable quicksort on the owner.
    vehicle_order = np.argsort(df_vehicles["owner_id"].to_numpy(), kind = "quicksort")

    vehicles = _from_pandas(df_vehicles, ["owner_id", "mode", "vehicle_id"])[vehicle_order].select(
        person_id = pl.col("owner_id"), vehicles = pl.concat_str([
            pl.lit('"'), _as_string("mode"), pl.lit('":"'), _as_string("vehicle_id"), pl.lit('"')
        ])
    ).group_by("person_id", maintain_order = True).agg(pl.col("vehicles").str.join(","))

    persons = persons.join(vehicles, on = "person_id", how = "left", maintain_order = "left")

    # Activities with their locations
    geometry = df_locations["geometry"].values

    locations = _from_pandas(df_locations, ["person_id", "activity_index", "location_id"]).with_columns(
        x = pl.Series(shapely.get_x(geometry)), y = pl.Series(shapely.get_y(geometry)),
    )

    activities = _from_pandas(df_activities, [
        "person_id", "activity_index", "purpose", "start_time", "end_time"
    ]).sort(["person_id", "activity_index"]).join(
        locations, on = ["person_id", "activity_index"], how = "left", maintain_order = "left"
    ).select(
        "person_id", _as_string("purpose"),
        pl.col("start_time", "end_time").cast(pl.Float64),
        "x", "y", _as_string("location_id"),
    ).join(persons.select("person_id", "p", "household_id"), on = "person_id", how = "left", maintain_order = "left")

    trips = _from_pandas(df_trips, ["person_id", "mode", "departure_time", "arrival_time"]).select(
        "person_id", _as_string("mode"),
        pl.col("departure_time").cast(pl.Float64),
        travel_time = (pl.col("arrival_time") - pl.col("departure_time")).cast(pl.Float64),
    ).join(persons.select("person_id", "p"), on = "person_id", how = "left", maintain_order = "left")

    assert activities["p"].null_count() == 0, "Found activities of unknown persons"
    assert trips["p"].null_count() == 0, "Found trips of unknown persons"

    # Output person order, keeping the order of the inputs within a person
    activities = activities.sort("p", maintain_order = True)
    trips = trips.sort("p", maintain_order = True)

    activity_counts = np.bincount(activities["p"].to_numpy(), minlength = len(persons))
    trip_counts = np.bincount(trips["p"].to_numpy(), minlength = len(persons))

    assert np.all(activity_counts > 0), "Found persons without activities"
    assert np.all(trip_counts == activity_counts - 1), "Number of trips does not match number of activities"

    return persons, activities, trips, activity_counts

def format_chunk(persons, activities, trips):
    """ Returns the XML text for a contiguous block of persons """
    header = persons.select(pl.concat_str(
        [pl.lit('  <person id="'), pl.col("person_id").cast(pl.String), pl.lit('">\n    <attributes>\n')]
        + _attribute("householdId", "java.lang.Integer", pl.col("household_id").cast(pl.String))
        + _attribute("householdIncome", "java.lang.Double", pl.col("household_income"))
        + _attribute("carAvailability", "java.lang.String", pl.col("car_availability"))
        + _attribute("bikeAvailability", "java.lang.String", pl.col("bike_availability"))
        # compatibility with standard MATSim
        + [pl.when(pl.col("car_availability") == "none")
           .then(pl.lit('      <attribute name="carAvail" class="java.lang.String">never</attribute>\n'))
           .otherwise(pl.lit(""))]
        # custom attribute for motorcycle availability
        + (_attribute("useMotorcycle", "java.lang.Boolean", pl.col("use_motorcycle"))
           if "use_motorcycle" in persons.columns else [])
        + _attribute("censusHouseholdId", "java.lang.Long", pl.col("census_household_id").cast(pl.String))
        + _attribute("censusPersonId", "java.lang.Long", pl.col("census_person_id").cast(pl.String))
        + _attribute("htsHouseholdId", "java.lang.Long", pl.col("hts_household_id").cast(pl.String))
        + _attribute("htsPersonId", "java.lang.Long", pl.col("hts_person_id").cast(pl.String))
        + _attribute("hasPtSubscription", "java.lang.Boolean", pl.col("has_pt_subscription"))
        + _attribute("hasLicense", "java.lang.String", pl.col("has_license"))
        + _attribute("isPassenger", "java.lang.Boolean", pl.col("is_passenger"))
        + _attribute("age", "java.lang.Integer", pl.col("age").cast(pl.String))
        + _attribute("employed", "java.lang.String", pl.col("employed"))
        + _attribute("sex", "java.lang.String", pl.col("sex"))
        + _attribute("vehicles", "org.matsim.vehicles.PersonVehicles",
            pl.concat_str([pl.lit("{"), pl.col("vehicles").fill_null(""), pl.lit("}")]))
        + [pl.lit('    </attributes>\n    <plan selected="yes">\n')]
    ).alias("text"))["text"]

    activity_text = activities.with_columns(
        x = format_float_f(activities["x"].to_numpy()),
        y = format_float_f(activities["y"].to_numpy()),
        start_time = format_time(activities["start_time"].to_numpy()),
        end_time = format_time(activities["end_time"].to_numpy()),
    ).select(pl.concat_str([
        pl.lit('      <activity type="'), pl.col("purpose"),
        pl.lit('" x="'), pl.col("x"), pl.lit('" y="'), pl.col("y"),
        pl.lit('" facility="'),
        pl.when(pl.col("purpose") == "home")
            .then(pl.concat_str([pl.lit("home_"), pl.col("household_id").cast(pl.String)]))
            .otherwise(pl.col("location_id")),
        pl.lit('" '),
        pl.concat_str([pl.lit('start_time="'), pl.col("start_time"), pl.lit('" ')]).fill_null(""),
        pl.concat_str([pl.lit('end_time="'), pl.col("end_time"), pl.lit('" ')]).fill_null(""),
        pl.lit("/>\n"),
    ]).alias("text"))["text"]

    leg_text = trips.with_columns(
        departure_time = format_time(trips["departure_time"].to_numpy()).fill_null("None"),
        travel_time = format_time(trips["travel_time"].to_numpy()).fill_null("None"),
    ).select(pl.concat_str([
        pl.lit('      <leg mode="'), pl.col("mode"),
        pl.lit('" dep_time="'), pl.col("departure_time"),
        pl.lit('" trav_time="'), pl.col("travel_time"),
        pl.lit('" >\n      <attributes>\n        <attribute name="routingMode" class="java.lang.String">'),
        pl.col("mode"),
        pl.lit("</attribute>\n      </attributes>\n      </leg>\n"),
    ]).alias("text"))["text"]

    # Interleave: the header precedes the first activity of a person, activity j is
    # followed by leg j and the last activity by the end of the plan. With n activities
    # and n - 1 legs per person, the leg row is the activity row minus the person row.
    p = activities["p"].to_numpy() - persons["p"][0]
    row = np.arange(len(p))

    is_first = np.r_[True, p[1:] != p[:-1]]
    is_last = np.r_[p[1:] != p[:-1], True]
    leg_row = np.where(is_last, 0, row - p)

    text = pl.select(pl.concat_str([
        pl.when(pl.lit(is_first)).then(header.gather(p)).otherwise(pl.lit("")),
        activity_text,
        pl.when(pl.lit(is_last)).then(pl.lit("    </plan>\n  </person>\n"))
            .otherwise(leg_text.gather(leg_row) if len(leg_text) > 0 else pl.lit("")),
    ]).alias("text"))["text"]

    return text.str.join("").item()

def write(output, persons, activities, trips, activity_counts, crs,
        workers = 1, chunk_size = CHUNK_SIZE, compress_level = COMPRESS_LEVEL, progress = None):
    """ Writes the gzipped population to a binary stream """
    activity_offsets = np.r_[0, np.cumsum(activity_counts)]
    trip_offsets = activity_offsets - np.arange(len(activity_offsets))

    def compress(text):
        return gzip.compress(text.encode("utf-8"), compresslevel = compress_level, mtime = 0)

    def process(start, end):
        return end - start, compress(format_chunk(
            persons.slice(start, end - start),
            activities.slice(activity_offsets[start], activity_offsets[end] - activity_offsets[start]),
            trips.slice(trip_offsets[start], trip_offsets[end] - trip_offsets[start]),
        ))

    # Start and end of the document are written by the generic writer
    buffer = io.BytesIO()
    writer = writers.PopulationWriter(buffer)
    writer.start_population({ "coordinateReferenceSystem": crs })
    output.write(compress(buffer.getvalue().decode("utf-8")))

    def collect(future):
        count, data = future.result()
        output.write(data)
        if progress is not None: progress.update(count)

    with ThreadPoolExecutor(max_workers = workers) as pool:
        pending = collections.deque()

        for start in range(0, len(persons), chunk_size):
            pending.append(pool.submit(process, start, min(start + chunk_size, len(persons))))

            # Bound the number of chunks held in memory
            while len(pending) > workers + 1:
                collect(pending.popleft())

        while len(pending) > 0:
            collect(pending.popleft())

    buffer.seek(0)
    buffer.truncate()
    writer.end_population()
    output.write(compress(buffer.getvalue().decode("utf-8")))

def execute(context):
    df_locations = context.stage("synthesis.population.spatial.locations")

    persons, activities, trips, activity_counts = prepare(
        context.stage("synthesis.population.enriched"),
        context.stage("synthesis.population.activities"),
        df_locations,
        context.stage("synthesis.population.trips"),
        context.stage("synthesis.vehicles.vehicles")[1],
    )

    with open("%s/population.xml.gz" % context.path(), "wb") as output:
        with context.progress(total = len(persons), label = "Writing population ...") as progress:
            write(output, persons, activities, trips, activity_counts, df_locations.crs,
                workers = context.config("processes"), progress = progress)

    return "population.xml.gz"
