import polars as pl

import matsim.writers as writers

"""
Writes the MATSim households (households.xml.gz).

The XML text is built column-wise with polars, see
matsim.writers.write_gzip_chunks.
"""

CHUNK_SIZE = 100_000 # households per chunk / gzip member

def configure(context):
    context.stage("synthesis.population.enriched")
    context.config("processes")

def prepare(df_persons):
    """ One row per household, with the attributes of its first person """
    persons = writers.from_pandas(df_persons, [
        "household_id", "person_id", "car_availability", "bike_availability", "census_household_id"
    ]).with_columns(
        household_income = writers.format_python_float(df_persons["household_income"].to_numpy()),
    ).sort(["household_id", "person_id"])

    return persons.group_by("household_id", maintain_order = True).agg(
        pl.first("car_availability", "bike_availability", "household_income", "census_household_id"),
        members = pl.concat_str([
            pl.lit('      <personId refId="'), pl.col("person_id").cast(pl.String), pl.lit('" />\n')
        ]).str.join(""),
    )

def format_chunk(households):
    return households.select(pl.concat_str(
        [pl.lit('  <household id="'), pl.col("household_id").cast(pl.String), pl.lit('">\n    <members>\n'),
         pl.col("members"), pl.lit("    </members>\n    <attributes>\n")]
        + writers.attribute("carAvailability", "java.lang.String", writers.as_string("car_availability"))
        + writers.attribute("bikeAvailability", "java.lang.String", writers.as_string("bike_availability"))
        + writers.attribute("household_income", "java.lang.Double", pl.col("household_income"))
        + writers.attribute("censusId", "java.lang.Long", pl.col("census_household_id").cast(pl.String))
        + [pl.lit("    </attributes>\n  </household>\n")]
    ).alias("text"))["text"].str.join("").item()

def write(output, households, workers = 1, chunk_size = CHUNK_SIZE, progress = None):
    """ Writes the gzipped households to a binary stream """
    header = writers.render(writers.HouseholdsWriter, lambda writer: writer.start_households())

    footer = writers.render(writers.HouseholdsWriter, lambda writer: writer.end_households(),
        scope = writers.HouseholdsWriter.HOUSEHOLDS_SCOPE, indent = 1)

    writers.write_gzip_chunks(output, header, footer, len(households),
        lambda start, end: format_chunk(households.slice(start, end - start)),
        workers = workers, chunk_size = chunk_size, progress = progress)

def execute(context):
    households = prepare(context.stage("synthesis.population.enriched"))

    with open("%s/households.xml.gz" % context.path(), "wb") as output:
        with context.progress(total = len(households), label = "Writing households ...") as progress:
            write(output, households, workers = context.config("processes"), progress = progress)

    return "households.xml.gz"
