import pandas as pd

def configure(context):
    method = context.config("vehicles_method", "default")

    if method == "default":
        context.stage("synthesis.vehicles.cars.default", alias = "cars")
        context.stage("synthesis.vehicles.motorcycles.default", alias = "motorcycles")
    elif method == "fleet_sample":
        context.stage("synthesis.vehicles.cars.fleet_sampling", alias = "cars")
        context.stage("synthesis.vehicles.motorcycles.fleet_sampling", alias = "motorcycles")
    else:
        raise RuntimeError("Unknown vehicles generation method : %s" % method)
    
    context.stage("synthesis.vehicles.passengers.default")

def execute(context):
    df_car_types, df_cars = context.stage("cars")
    df_motorcycle_types, df_motorcycles = context.stage("motorcycles")
    df_passenger_types, df_passengers = context.stage("synthesis.vehicles.passengers.default")

    df_vehicles = pd.concat([df_cars, df_motorcycles, df_passengers])
    df_types = pd.concat([df_car_types, df_motorcycle_types, df_passenger_types])

    return df_types, df_vehicles
