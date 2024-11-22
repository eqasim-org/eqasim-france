import re
import pandas as pd
import numpy as np
from datetime import date

"""
Creates the synthetic vehicle fleet
"""

def configure(context):
    context.stage("synthesis.population.enriched")
    context.stage("synthesis.population.spatial.home.zones")
    context.stage("data.vehicles.raw")
    context.stage("data.vehicles.types")

    context.config("vehicles_year", 2021)

def _sample_vehicle(context, args):
    vehicle = args
    year = context.config("vehicles_year")
    df_vehicle_fleet_counts, df_vehicle_age_counts = context.data("fleet"), context.data("age")

    commune_id = vehicle["commune_id"]

    if  commune_id in df_vehicle_fleet_counts["commune_id"].unique():
        fleet = df_vehicle_fleet_counts.loc[df_vehicle_fleet_counts["commune_id"] == commune_id]
        choice = fleet.sample(weights="fleet")
        critair = choice["critair"].values[0]
        technology = choice["technology"].values[0]

        age_mask = (df_vehicle_age_counts["critair"] == critair) & (df_vehicle_age_counts["technology"] == technology)
        age = df_vehicle_age_counts.loc[age_mask].sample(weights="fleet")["age"].values[0]
    else:
        choice = df_vehicle_age_counts.sample(weights="fleet")
        critair = choice["critair"].values[0]
        technology = choice["technology"].values[0]
        age = choice["age"].values[0]

    vehicle["critair"] = critair
    vehicle["technology"] = technology
    vehicle["age"] = age

    euro = _get_euro_from_critair(vehicle, year)
    vehicle["euro"] = euro

    if technology == "Gazole":
        hbefa_tech = "diesel"
        vehicle["type_id"] = "car_%s_%s" % (hbefa_tech, euro)
    if technology == "Essence":
        hbefa_tech = "petrol"
        vehicle["type_id"] = "car_%s_%s" % (hbefa_tech, euro)

    context.progress.update()
    return vehicle

def _get_euro_from_critair(vehicle, year):

    critair = vehicle["critair"]  # Crit'air 1, Crit'air 2, ..., Crit'air 5, Crit'air E, Non classée
    technology = vehicle["technology"]  # Gazole, Essence, Electrique et hydrogène, Essence hybride rechargeable, Gaz, Gazole hybride rechargeable
    age = vehicle["age"]  # 0 ans, 1 ans, ..., 19 ans, >20 ans

    # we are using the following table : https://www.ecologie.gouv.fr/sites/default/files/Tableau_classification_des_vehicules.pdf
    age_num = re.findall(r'\d+', age)
    if len(age_num) == 0:
        raise RuntimeError("Badly formatted 'age' variable found for vehicle (id: %s) : %s" % (age, vehicle["vehicle_id"]))

    birthday = int(year) - int(age_num[0])

    euro = 1

    # set minimum value based on birthday
    if 1997 <= birthday < 2001:
        euro = 2
    if 2001 <= birthday < 2006:
        euro = 3
    if 2006 <= birthday < 2011:
        euro = 4
    if 2011 <= birthday < 2016:
        euro = 5
    if birthday >= 2016:
        euro = 6

    # refine based on critair
    if critair == "Crit'air E" or technology == "Electrique et hydrogène":
        euro = max(euro, 6)
    if critair == "Crit'air 1" and (technology == "Gaz" or "hybride" in technology):
        euro = max(euro, 6)
    if critair == "Crit'air 1" and technology == "Essence":
        euro = max(euro, 5)  # or 6 in table
    if critair == "Crit'air 2" and technology == "Essence":
        euro = max(euro, 4)
    if critair == "Crit'air 2" and technology == "Gazole":
        euro = max(euro, 5)  # or 6 in table
    if critair == "Crit'air 3" and technology == "Essence":
        euro = max(euro, 2) # or 3 in table
    if critair == "Crit'air 3" and technology == "Gazole":
        euro = max(euro, 4)
    if critair == "Crit'air 4" and technology == "Gazole":
        euro = max(euro, 3)
    if critair == "Crit'air 5" and technology == "Gazole":
        euro = max(euro, 2)
    if critair == "Non classée" and technology == "Gazole":
        euro = max(euro, 1)

    euro = str(euro)
    if euro == '6':
        if 2016 <= birthday < 2019:
            euro = '6ab'
        else:
            euro = '6c'

    return euro

def execute(context):

    df_vehicle_types = context.stage("data.vehicles.types")

    df_persons = context.stage("synthesis.population.enriched")
    df_homes = context.stage("synthesis.population.spatial.home.zones")

    df_vehicles = pd.merge(df_persons[["household_id", "person_id"]], df_homes[["household_id", "commune_id"]], on = "household_id")

    df_vehicles = df_vehicles.rename(columns = { "person_id": "owner_id" })
    df_vehicles["vehicle_id"] = df_vehicles["owner_id"].astype(str) + ":car"
    df_vehicles = df_vehicles.drop_duplicates("vehicle_id") # is this needed?
    df_vehicles["type_id"] = "default_car"
    df_vehicles["mode"] = "car"

    df_vehicle_fleet_counts, df_vehicle_age_counts = context.stage("data.vehicles.raw")

    res = []

    with context.progress(label = "Processing vehicles data ...", total = len(df_vehicles)) as progress:
        with context.parallel(dict(fleet = df_vehicle_fleet_counts, age = df_vehicle_age_counts)) as parallel:
            for df_partial in parallel.imap(_sample_vehicle, df_vehicles.to_dict(orient="records")):
                res.append(df_partial)

    df_vehicles = pd.DataFrame.from_dict(res)

    return df_vehicle_types, df_vehicles