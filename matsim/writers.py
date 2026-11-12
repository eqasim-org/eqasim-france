import collections
import gzip
import io
from concurrent.futures import ThreadPoolExecutor
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
import polars as pl

class XmlWriter:
    def __init__(self, writer):
        self.writer = writer
        self.indent = 0
        self.scope = None

    def _write_line(self, content):
        self._write_indent()
        self._write(content + "\n")

    def _write_indent(self):
        self._write("  " * self.indent)

    def _write(self, content):
        self.writer.write(bytes(content, "utf-8"))

    def _require_scope(self, scope):
        if scope == None and not self.scope is None:
            raise RuntimeError("Execpted initial scope")

        if not self.scope == scope:
            raise RuntimeError("Expected different scope")

    def yes_no(self, value):
        return "yes" if value else "no"

    def true_false(self, value):
        return "true" if value else "false"

    def time(self, time):
        if np.isnan(time):
            return None

        time = int(time)
        hours = time // 3600
        minutes = (time % 3600) // 60
        seconds = (time % 60)
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    def location(self, x, y, facility_id = None):
        return (x, y, None if facility_id is None else facility_id)

def _write_preface_attributes(writer, attributes):
    if len(attributes) > 0:
        writer._write_line('<attributes>')
        writer.indent += 1

        for item in attributes.items():
            writer._write_line('<attribute name="%s" class="java.lang.String">%s</attribute>' % item)

        writer.indent -= 1
        writer._write_line('</attributes>')

class PopulationWriter(XmlWriter):
    POPULATION_SCOPE = 0
    FINISHED_SCOPE = 1
    PERSON_SCOPE = 2
    PLAN_SCOPE = 3
    ATTRIBUTES_SCOPE = 4

    def __init__(self, writer):
        XmlWriter.__init__(self, writer)

    def start_population(self, attributes = {}):
        self._require_scope(None)
        self._write_line('<?xml version="1.0" encoding="utf-8"?>')
        self._write_line('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">')
        self._write_line('<population>')

        self.scope = self.POPULATION_SCOPE
        self.indent += 1

        _write_preface_attributes(self, attributes)

    def end_population(self):
        self._require_scope(self.POPULATION_SCOPE)
        self.indent -= 1
        self._write_line('</population>')
        self.scope = self.FINISHED_SCOPE

    def start_person(self, person_id):
        self._require_scope(self.POPULATION_SCOPE)
        self._write_line('<person id="%d">' % person_id)
        self.scope = self.PERSON_SCOPE
        self.indent += 1

    def end_person(self):
        self._require_scope(self.PERSON_SCOPE)
        self.indent -= 1
        self.scope = self.POPULATION_SCOPE
        self._write_line('</person>')

    def start_attributes(self):
        # We don't require any scope here because attributes can be almost anywhere
        self._write_line('<attributes>')
        self.indent += 1
        # And we need to remember which scope we were in before starting the attributes
        self._pre_attributes_scope = self.scope
        self.scope = self.ATTRIBUTES_SCOPE

    def end_attributes(self):
        self._require_scope(self.ATTRIBUTES_SCOPE)
        self.indent -= 1
        # Resetting the scope that we were in before starting the attributes
        self.scope = self._pre_attributes_scope
        self._write_line('</attributes>')

    def add_attribute(self, name, type, value):
        self._require_scope(self.ATTRIBUTES_SCOPE)
        self._write_line('<attribute name="%s" class="%s">%s</attribute>' % (
            name, type, value
        ))

    def start_plan(self, selected):
        self._require_scope(self.PERSON_SCOPE)
        self._write_line('<plan selected="%s">' % self.yes_no(selected))
        self.indent += 1
        self.scope = self.PLAN_SCOPE

    def end_plan(self):
        self._require_scope(self.PLAN_SCOPE)
        self.indent -= 1
        self.scope = self.PERSON_SCOPE
        self._write_line('</plan>')

    def add_activity(self, type, location, start_time = None, end_time = None):
        self._require_scope(self.PLAN_SCOPE)

        self._write_indent()
        self._write('<activity ')
        self._write('type="%s" ' % type)
        self._write('x="%f" y="%f" ' % (location[0], location[1]))
        if location[2] is not None: self._write('facility="%s" ' % str(location[2]))
        if start_time is not None: self._write('start_time="%s" ' % self.time(start_time))
        if end_time is not None: self._write('end_time="%s" ' % self.time(end_time))
        self._write('/>\n')

    def add_leg(self, mode, departure_time, travel_time):
        self._require_scope(self.PLAN_SCOPE)

        self._write_indent()
        self._write('<leg ')
        self._write('mode="%s" ' % mode)
        self._write('dep_time="%s" ' % self.time(departure_time))
        self._write('trav_time="%s" ' % self.time(travel_time))
        self._write('>\n')
        self.start_attributes()
        self.add_attribute('routingMode', 'java.lang.String', mode)
        self.end_attributes()
        self._write_line('</leg>')

class HouseholdsWriter(XmlWriter):
    HOUSEHOLDS_SCOPE = 0
    FINISHED_SCOPE = 1
    HOUSEHOLD_SCOPE = 2
    ATTRIBUTES_SCOPE = 3

    def __init__(self, writer):
        XmlWriter.__init__(self, writer)

    def start_households(self, attributes = {}):
        self._require_scope(None)
        self._write_line('<?xml version="1.0" encoding="utf-8"?>')
        self._write_line('<households xmlns="http://www.matsim.org/files/dtd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.matsim.org/files/dtd http://www.matsim.org/files/dtd/households_v1.0.xsd">')

        self.scope = self.HOUSEHOLDS_SCOPE
        self.indent += 1

        _write_preface_attributes(self, attributes)

    def end_households(self):
        self._require_scope(self.HOUSEHOLDS_SCOPE)
        self._write_line('</households>')
        self.scope = self.FINISHED_SCOPE

    def start_household(self, household_id):
        self._require_scope(self.HOUSEHOLDS_SCOPE)
        self._write_line('<household id="%d">' % household_id)
        self.scope = self.HOUSEHOLD_SCOPE
        self.indent += 1

    def end_household(self):
        self._require_scope(self.HOUSEHOLD_SCOPE)
        self.indent -= 1
        self.scope = self.HOUSEHOLDS_SCOPE
        self._write_line('</household>')

    def start_attributes(self):
        self._require_scope(self.HOUSEHOLD_SCOPE)
        self._write_line('<attributes>')
        self.indent += 1
        self.scope = self.ATTRIBUTES_SCOPE

    def end_attributes(self):
        self._require_scope(self.ATTRIBUTES_SCOPE)
        self.indent -= 1
        self.scope = self.HOUSEHOLD_SCOPE
        self._write_line('</attributes>')

    def add_attribute(self, name, type, value):
        self._require_scope(self.ATTRIBUTES_SCOPE)
        self._write_line('<attribute name="%s" class="%s">%s</attribute>' % (
            name, type, value
        ))

    def add_members(self, person_ids):
        self._require_scope(self.HOUSEHOLD_SCOPE)
        self._write_line('<members>')
        self.indent += 1
        for person_id in person_ids: self._write_line('<personId refId="%s" />' % person_id)
        self.indent -= 1
        self._write_line('</members>')

    def add_income(self, income):
        self._require_scope(self.HOUSEHOLD_SCOPE)
        self._write_line('<income currency="CHF" period="month">%f</income>' % income)

class FacilitiesWriter(XmlWriter):
    FACILITIES_SCOPE = 0
    FINISHED_SCOPE = 1
    FACILITY_SCOPE = 2

    def __init__(self, writer):
        XmlWriter.__init__(self, writer)

    def start_facilities(self, attributes = {}):
        self._require_scope(None)
        self._write_line('<?xml version="1.0" encoding="utf-8"?>')
        self._write_line('<!DOCTYPE facilities SYSTEM "http://www.matsim.org/files/dtd/facilities_v1.dtd">')
        self._write_line('<facilities>')

        self.scope = self.FACILITIES_SCOPE
        self.indent += 1

        _write_preface_attributes(self, attributes)

    def end_facilities(self):
        self._require_scope(self.FACILITIES_SCOPE)
        self.indent -= 1
        self._write_line('</facilities>')
        self.scope = self.FINISHED_SCOPE

    def start_facility(self, facility_id, x, y):
        self._require_scope(self.FACILITIES_SCOPE)
        self._write_line('<facility id="%s" x="%f" y="%f">' % (
            str(facility_id), x, y
        ))

        self.indent += 1
        self.scope = self.FACILITY_SCOPE

    def end_facility(self):
        self._require_scope(self.FACILITY_SCOPE)
        self.indent -= 1
        self.scope = self.FACILITIES_SCOPE
        self._write_line('</facility>')

    def add_activity(self, purpose):
        self._require_scope(self.FACILITY_SCOPE)
        self._write_line('<activity type="%s" />' % purpose)


class VehiclesWriter(XmlWriter):
    VEHICLES_SCOPE = 0
    FINISHED_SCOPE = 1

    def __init__(self, writer):
        XmlWriter.__init__(self, writer)

    def start_vehicles(self, attributes = {}):
        self._require_scope(None)
        self._write_line('<?xml version="1.0" encoding="utf-8"?>')
        self._write_line('<vehicleDefinitions xmlns="http://www.matsim.org/files/dtd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.matsim.org/files/dtd http://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd">')

        self.scope = self.VEHICLES_SCOPE
        self.indent += 1

        _write_preface_attributes(self, attributes)

    def end_vehicles(self):
        self._require_scope(self.VEHICLES_SCOPE)
        self.indent -= 1
        self._write_line('</vehicleDefinitions>')
        self.scope = self.FINISHED_SCOPE

    def add_type(self, vehicle_type_id, nb_seats = 4, length = 5.0, width = 1.0, pce = 1.0, mode = "car", attributes = {}, engine_attributes = {}):
        self._require_scope(self.VEHICLES_SCOPE)
        self._write_line('<vehicleType id="%s">' % str(vehicle_type_id))

        self.indent += 1

        if len(attributes) > 0:
            self._write_line('<attributes>')
            self.indent += 1
            for key, item in attributes.items():
                self._write_line('<attribute name="%s" class="java.lang.String">%s</attribute>' % (key, escape(item)))
            self.indent -= 1
            self._write_line('</attributes>')

        if not np.isnan(nb_seats):
            self._write_line('<capacity seats="%d" standingRoomInPersons="0" />' % nb_seats)

        self._write_line('<length meter="%f"/>' % length)
        self._write_line('<width meter="%f"/>' % width)

        if len(engine_attributes) > 0:
            self._write_line('<engineInformation>')
            self.indent += 1
            self._write_line('<attributes>')
            self.indent += 1
            for key, item in engine_attributes.items():
                self._write_line('<attribute name="%s" class="java.lang.String">%s</attribute>' % (key, escape(item)))
            self.indent -= 1
            self._write_line('</attributes>')
            self.indent -= 1
            self._write_line('</engineInformation>')

        if not np.isnan(pce):
            self._write_line('<passengerCarEquivalents pce="%f"/>' % pce)

        self._write_line('<networkMode networkMode="%s"/>' % mode)

        self.indent -= 1
        self._write_line('</vehicleType>')


    def add_vehicle(self, vehicle_id, type_id, attributes = {}):
        self._require_scope(self.VEHICLES_SCOPE)

        if len(attributes) > 0:
            self._write_line('<vehicle id="%s" type="%s">' % (str(vehicle_id), str(type_id)))
            self.indent += 1
            self._write_line('<attributes>')
            self.indent += 1
            for key, item in attributes.items():
                self._write_line('<attribute name="%s" class="java.lang.String">%s</attribute>' % (str(key), str(item)))
            self.indent -= 1
            self._write_line('</attributes>')
            self.indent -= 1
            self._write_line('</vehicle>')
        else:
            self._write_line('<vehicle id="%s" type="%s" />' % (str(vehicle_id), str(type_id)))


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

# Vectorized formatting helpers, equivalent to the Python formatting of the writers above

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

def choose(mask, if_true, if_false):
    """ String series with if_true where mask is set, if_false elsewhere """
    return pl.select(pl.when(pl.lit(np.asarray(mask, dtype = bool)))
        .then(pl.lit(if_true)).otherwise(pl.lit(if_false))).to_series()

def format_python_bool(values):
    """ Vectorized str(value) for a boolean column """
    values = pd.Series(values)

    if values.dtype == bool:
        return choose(values.to_numpy(), "True", "False")

    return pl.Series([str(value) for value in values]) # e.g. object columns with NaN

def from_pandas(df, columns):
    """ Converts columns of a pandas frame to polars (Arrow strings and categories stay as they are) """
    return pl.from_pandas(pd.DataFrame(df[columns]), include_index = False)

def as_string(column):
    """ Equivalent of str(value) for string / categorical columns, as written before """
    return pl.col(column).cast(pl.String).fill_null("nan")

def attribute(name, java_class, value, indent = 3):
    """ Parts of a concat_str for an attribute line, value being an expression """
    return [
        pl.lit('%s<attribute name="%s" class="%s">' % ("  " * indent, name, java_class)),
        value, pl.lit("</attribute>\n")
    ]

# Chunked writing

COMPRESS_LEVEL = 9

def render(writer_class, build, scope = None, indent = 0):
    """ Returns the text that build(writer) writes with one of the writers above """
    buffer = io.BytesIO()
    writer = writer_class(buffer)
    writer.scope, writer.indent = scope, indent
    build(writer)
    return buffer.getvalue().decode("utf-8")

def write_gzip_chunks(output, header, footer, size, format_rows,
        workers = 1, chunk_size = 100_000, compress_level = COMPRESS_LEVEL, progress = None):
    """ Writes a gzipped document whose body is formatted in chunks of rows

    format_rows(start, end) returns the text for rows [start, end). Chunks are
    formatted and compressed in a thread pool (polars and zlib release the GIL)
    and each chunk becomes its own gzip member. Concatenated members are a valid
    gzip stream for Python, zcat and Java's GZIPInputStream (thus MATSim).
    """
    def compress(text):
        return gzip.compress(text.encode("utf-8"), compresslevel = compress_level, mtime = 0)

    def process(start, end):
        return end - start, compress(format_rows(start, end))

    def collect(future):
        count, data = future.result()
        output.write(data)
        if progress is not None: progress.update(count)

    output.write(compress(header))

    with ThreadPoolExecutor(max_workers = workers) as pool:
        pending = collections.deque()

        for start in range(0, size, chunk_size):
            pending.append(pool.submit(process, start, min(start + chunk_size, size)))

            # Bound the number of chunks held in memory
            while len(pending) > workers + 1:
                collect(pending.popleft())

        while len(pending) > 0:
            collect(pending.popleft())

    output.write(compress(footer))
