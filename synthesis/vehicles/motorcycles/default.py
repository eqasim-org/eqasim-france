import re
import pandas as pd

"""
Creates a motorcycle fleet based on a default vehicle type
"""

def configure(context):
    context.stage("synthesis.population.enriched")

def execute(context):
    df_persons = context.stage("synthesis.population.enriched")
    
    default_motorcycle_type = {
        'type_id': 'default_motorcycle', 'nb_seats': 1, 'length': 2.0, 'width': 1.0, 'pce': 1.0, 'mode': "motorcycle",
        'hbefa_cat': "motorcycle", 'hbefa_tech': "average", 'hbefa_size': "average", 'hbefa_emission': "average",
    }
    df_motorcyle_types = pd.DataFrame.from_records([default_motorcycle_type])

    df_vehicles = df_persons[["person_id"]].copy()
    df_vehicles = df_vehicles.rename(columns = { "person_id": "owner_id" })
    
    df_vehicles["mode"] = "motorcycle"

    df_vehicles["vehicle_id"] = df_vehicles["owner_id"].astype(str) + ":motorcycle"
    df_vehicles["type_id"] = "default_motorcycle"
    df_vehicles["critair"] = "Crit'air 1"
    df_vehicles["technology"] = "Essence"
    df_vehicles["age"] = 0
    df_vehicles["euro"] = 4

    return df_motorcyle_types, df_vehicles