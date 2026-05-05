import pandas as pd

def configure(context):
    method = context.config("vehicles_method", "default")
    with_motorcycles = context.config("with_motorcycles", False)

    if method == "default":
        context.stage("synthesis.vehicles.cars.default", alias = "cars")
        context.stage("synthesis.vehicles.motorcycles.default", alias = "motorcycles")
    elif method == "fleet_sample":
        context.stage("synthesis.vehicles.cars.fleet_sampling", alias = "cars")
        if with_motorcycles:
            context.stage("synthesis.vehicles.motorcycles.fleet_sampling", alias = "motorcycles")
        else:
            context.stage("synthesis.vehicles.motorcycles.default", alias = "motorcycles")
    else:
        raise RuntimeError("Unknown vehicles generation method : %s" % method)
    
    context.stage("synthesis.vehicles.passengers.default")

def execute(context):
    with_motorcycles = context.config("with_motorcycles")
    
    df_car_types, df_cars = context.stage("cars")
    df_passenger_types, df_passengers = context.stage("synthesis.vehicles.passengers.default")
    
    df_vehicles = pd.concat([df_cars, df_passengers])
    df_types = pd.concat([df_car_types, df_passenger_types])

    if with_motorcycles:
        df_motorcycle_types, df_motorcycles = context.stage("motorcycles")

        df_vehicles = pd.concat([df_vehicles, df_motorcycles])
        df_types = pd.concat([df_types, df_motorcycle_types])
    
    return df_types, df_vehicles
