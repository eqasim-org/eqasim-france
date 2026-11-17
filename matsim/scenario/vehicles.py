import polars as pl

import matsim.writers as writers

"""
Writes the MATSim vehicles (vehicles.xml.gz).

The few vehicle types are written by the generic writer, the vehicles are
built column-wise with polars, see matsim.writers.write_gzip_chunks.
"""

CHUNK_SIZE = 10_000 # vehicles per chunk / gzip member, small chunks bound memory and balance the threads

def configure(context):
    context.stage("synthesis.vehicles.vehicles")
    context.config("processes")

VEHICLE_ATTRIBUTES = ["critair", "technology", "age", "euro"]

def add_types(writer, df_vehicle_types):
    for type in df_vehicle_types.to_dict(orient = "records"):
        writer.add_type(
            type["type_id"],
            length = type["length"],
            width = type["width"],
            mode = type["mode"],
            attributes = {
                "CnossosCategory": type["cnossos_cat"],
            },
            engine_attributes = {
                "HbefaVehicleCategory": type["hbefa_cat"],
                "HbefaTechnology": type["hbefa_tech"],
                "HbefaSizeClass": type["hbefa_size"],
                "HbefaEmissionsConcept": type["hbefa_emission"]
            }
        )

def prepare(df_vehicles):
    return writers.from_pandas(df_vehicles, ["vehicle_id", "type_id"] + VEHICLE_ATTRIBUTES)

def format_chunk(vehicles):
    attributes = []

    for name in VEHICLE_ATTRIBUTES:
        attributes += writers.attribute(name, "java.lang.String", writers.as_string(name))

    return vehicles.select(pl.concat_str(
        [pl.lit('  <vehicle id="'), writers.as_string("vehicle_id"),
         pl.lit('" type="'), writers.as_string("type_id"), pl.lit('">\n    <attributes>\n')]
        + attributes
        + [pl.lit("    </attributes>\n  </vehicle>\n")]
    ).alias("text"))["text"].str.join("").item()

def write(output, df_vehicle_types, vehicles, workers = 1, chunk_size = CHUNK_SIZE, progress = None):
    """ Writes the gzipped vehicles to a binary stream """
    def build_header(writer):
        writer.start_vehicles()
        add_types(writer, df_vehicle_types)

    header = writers.render(writers.VehiclesWriter, build_header)

    footer = writers.render(writers.VehiclesWriter, lambda writer: writer.end_vehicles(),
        scope = writers.VehiclesWriter.VEHICLES_SCOPE, indent = 1)

    writers.write_gzip_chunks(output, header, footer, len(vehicles),
        lambda start, end: format_chunk(vehicles.slice(start, end - start)),
        workers = workers, chunk_size = chunk_size, progress = progress)

def execute(context):
    df_vehicle_types, df_vehicles = context.stage("synthesis.vehicles.vehicles")
    vehicles = prepare(df_vehicles)

    with open("%s/vehicles.xml.gz" % context.path(), "wb") as output:
        with context.progress(total = len(vehicles), label = "Writing vehicles ...") as progress:
            write(output, df_vehicle_types, vehicles, workers = context.config("processes"), progress = progress)

    return "vehicles.xml.gz"
