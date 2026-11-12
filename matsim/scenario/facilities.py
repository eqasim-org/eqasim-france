import polars as pl
import shapely

import matsim.writers as writers

"""
Writes the MATSim facilities (facilities.xml.gz): homes, then primary (work
and education), then secondary locations.

The XML text is built column-wise with polars, see
matsim.writers.write_gzip_chunks.
"""

CHUNK_SIZE = 100_000 # facilities per chunk / gzip member

def configure(context):
    context.stage("synthesis.locations.secondary")
    context.stage("synthesis.population.spatial.home.locations")
    context.stage("synthesis.population.spatial.primary.locations")
    context.config("processes")

def _activity(purpose):
    return '    <activity type="%s" />\n' % purpose

def _facilities(df, columns, identifier, activities):
    geometry = df["geometry"].values

    return writers.from_pandas(df, columns).select(
        id = identifier,
        x = writers.format_float_f(shapely.get_x(geometry)),
        y = writers.format_float_f(shapely.get_y(geometry)),
        activities = activities,
    )

def prepare(df_homes, df_work, df_education, df_secondary):
    """ One row per facility, in output order """
    homes = _facilities(df_homes, ["household_id"],
        pl.concat_str([pl.lit("home_"), pl.col("household_id").cast(pl.String)]),
        pl.lit(_activity("home")))

    work = _facilities(df_work.drop_duplicates("location_id"), ["location_id"],
        writers.as_string("location_id"), pl.lit(_activity("work")))

    education = _facilities(df_education.drop_duplicates("location_id"), ["location_id"],
        writers.as_string("location_id"), pl.lit(_activity("education")))

    secondary = _facilities(df_secondary, ["location_id", "offers_shop", "offers_leisure", "offers_other"],
        writers.as_string("location_id"), pl.concat_str([
            pl.when(pl.col("offers_%s" % purpose)).then(pl.lit(_activity(purpose))).otherwise(pl.lit(""))
            for purpose in ("shop", "leisure", "other")
        ]))

    return pl.concat([homes, work, education, secondary])

def format_chunk(facilities):
    return facilities.select(pl.concat_str([
        pl.lit('  <facility id="'), pl.col("id"), pl.lit('" x="'), pl.col("x"), pl.lit('" y="'), pl.col("y"),
        pl.lit('">\n'), pl.col("activities"), pl.lit("  </facility>\n"),
    ]).alias("text"))["text"].str.join("").item()

def write(output, facilities, crs, workers = 1, chunk_size = CHUNK_SIZE, progress = None):
    """ Writes the gzipped facilities to a binary stream """
    header = writers.render(writers.FacilitiesWriter,
        lambda writer: writer.start_facilities({ "coordinateReferenceSystem": crs }))

    footer = writers.render(writers.FacilitiesWriter, lambda writer: writer.end_facilities(),
        scope = writers.FacilitiesWriter.FACILITIES_SCOPE, indent = 1)

    writers.write_gzip_chunks(output, header, footer, len(facilities),
        lambda start, end: format_chunk(facilities.slice(start, end - start)),
        workers = workers, chunk_size = chunk_size, progress = progress)

def execute(context):
    df_homes = context.stage("synthesis.population.spatial.home.locations")
    df_work, df_education = context.stage("synthesis.population.spatial.primary.locations")
    df_secondary = context.stage("synthesis.locations.secondary")

    facilities = prepare(df_homes, df_work, df_education, df_secondary)

    with open("%s/facilities.xml.gz" % context.path(), "wb") as output:
        with context.progress(total = len(facilities), label = "Writing facilities ...") as progress:
            write(output, facilities, df_homes.crs, workers = context.config("processes"), progress = progress)

    return "facilities.xml.gz"
