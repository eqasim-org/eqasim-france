import io, gzip

import numpy as np
import pandas as pd

import matsim.writers as writers

def configure(context):
    context.stage("synthesis.vehicles.vehicles")

TYPE_FIELDS = ["type_id", "nb_seats", "length", "width", "pce", "mode"]
VEHICLE_FIELDS = ["vehicle_id", "type_id", "critair", "technology", "age", "euro"]

def execute(context):
    output_path = "%s/vehicles.xml.gz" % context.path()

    df_vehicle_types, df_vehicles = context.stage("synthesis.vehicles.vehicles")

    with gzip.open(output_path, 'wb+') as writer:
        with io.BufferedWriter(writer, buffer_size = 2 * 1024**3) as writer:
            writer = writers.VehiclesWriter(writer)
            writer.start_vehicles()

            with context.progress(total = len(df_vehicle_types), label = "Writing vehicles types ...") as progress:
                for type in df_vehicle_types.to_dict(orient="records"):
                    writer.add_type(
                        type["type_id"],
                        length=type["length"],
                        width=type["width"],
                        engine_attributes = {
                            "HbefaVehicleCategory": type["hbefa_cat"],
                            "HbefaTechnology": type["hbefa_tech"],
                            "HbefaSizeClass": type["hbefa_size"],
                            "HbefaEmissionsConcept": type["hbefa_emission"]
                        }
                    )
                    progress.update()

            with context.progress(total = len(df_vehicles), label = "Writing vehicles ...") as progress:
                for vehicle in df_vehicles.to_dict(orient="records"):

                    writer.add_vehicle(
                        vehicle["vehicle_id"],
                        vehicle["type_id"],
                        attributes = {
                            "critair": vehicle["critair"],
                            "technology": vehicle["technology"],
                            "age": vehicle["age"],
                            "euro": vehicle["euro"]
                        }
                    )
                    progress.update()

            writer.end_vehicles()

    return "vehicles.xml.gz"