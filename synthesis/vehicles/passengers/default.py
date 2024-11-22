import re
import pandas as pd

"""
Creates a vehicle fleet based on a default vehicle type for the dummy passenger mode
"""

def configure(context):
    context.stage("synthesis.population.enriched")

def execute(context):
    df_persons = context.stage("synthesis.population.enriched")

    df_vehicle_types = pd.DataFrame.from_records([{
        "type_id": "default_car_passenger", "nb_seats": 4, "length": 5.0, "width": 1.0, "pce": 1.0, "mode": "car_passenger",
        "hbefa_cat": "PASSENGER_CAR", "hbefa_tech": "average", "hbefa_size": "average", "hbefa_emission": "average",
    }])

    df_vehicles = df_persons[["person_id"]].copy()
    df_vehicles = df_vehicles.rename(columns = { "person_id": "owner_id" })
    
    df_vehicles["mode"] = "car_passenger"

    df_vehicles["vehicle_id"] = df_vehicles["owner_id"].astype(str) + ":car_passenger"
    df_vehicles["type_id"] = "default_car_passenger"
    df_vehicles["critair"] = "Crit'air 1"
    df_vehicles["technology"] = "Gazole"
    df_vehicles["age"] = 0
    df_vehicles["euro"] = 6

    return df_vehicle_types, df_vehicles