import re
import pandas as pd
import numpy as np
from datetime import date

from synpp import ConfigurationContext, ExecuteContext, ParallelSlaveContext

"""
Creates the synthetic motorcycle fleet
"""

def configure(context: ConfigurationContext):
    context.stage("synthesis.population.enriched")
    context.stage("synthesis.population.spatial.home.zones")
    context.stage("data.vehicles.motorcycles.2rm")
    context.stage("data.vehicles.motorcycles.types")

    context.config("vehicles_year", 2021)

def _sample_vehicle(context: ParallelSlaveContext, args):
    vehicle = args
    year = context.config("vehicles_year")
    df_motorcycle_fleet_counts = context.data("fleet")

    fleet = df_motorcycle_fleet_counts.loc[
        (df_motorcycle_fleet_counts["AGECAT"] == vehicle["agecat"]) &
        (df_motorcycle_fleet_counts["SEXE"] == vehicle["sex"])
    ]

    if len(fleet) == 0:
        # Default values
        vehicle["mode"] = "motorcycle"
        vehicle["type_id"] = "default_motorcycle"
        vehicle["critair"] = "Crit'air 1"
        vehicle["technology"] = "Essence"
        vehicle["age"] = 0
        vehicle["euro"] = 4
        context.progress.update()
        return vehicle

    choice = fleet.sample(weights="POIDSVEHICULE")

    vehicle_age = choice["AGEVEHICULE"].values[0]
    vehicle_birthday = int(year) - int(vehicle_age)
    vehicle_engine = choice["MOTEUR"].values[0]
    vehicle_engine_size = choice["PFCAT"].values[0]
    vehicle_type_id = "default_motorcycle"
    
    euro = 0
    critair = -1

    if vehicle_engine == "Electric":
        euro = 0
        critair = 1
    else:
        # set minimum value based on birthday
        if 2000 <= vehicle_birthday < 2004:
            euro = 1
            critair = 4
        if 2004 <= vehicle_birthday < 2007:
            euro = 2
            critair = 3
        if 2007 <= vehicle_birthday < 2017:
            euro = 3
            critair = 2
        if 2017 <= vehicle_birthday < 2021:
            euro = 4
            critair = 1
        if vehicle_birthday >= 2021:
            euro = 5
            critair = 1

    vehicle["critair"] = "Crit'air %d" % critair
    vehicle["age"] = vehicle_age
    vehicle["euro"] = str(euro)
    vehicle["technology"] = "Essence" if vehicle_engine in ["2S", "4S"] else "Electrique"

    if vehicle_engine == "Electric":
        vehicle_type_id = "motorcycle_electric"
    else:
        if vehicle_engine_size == "0_50cc":
            vehicle_type_id = "motorcycle_lte_50cc_50kmh_euro_%d_cnossos_4a" % euro
        elif vehicle_engine_size == "50_125cc":
            vehicle_type_id = "motorcycle_lte_250cc_%s_euro_%d_cnossos_4a" % (vehicle_engine, euro)
        elif vehicle_engine_size == "125_250cc":
            vehicle_type_id = "motorcycle_lte_250cc_%s_euro_%d_cnossos_4b" % (vehicle_engine, euro)
        else:
            vehicle_type_id = "motorcycle_gt_250cc_4S_euro_%d_cnossos_4b" % euro

    vehicle["type_id"] = vehicle_type_id

    context.progress.update()
    return vehicle

def execute(context: ExecuteContext):

    df_motorcycle_types = context.stage("data.vehicles.motorcycles.types")
    df_motorcycles_fleet_counts, age_bins = context.stage("data.vehicles.motorcycles.2rm")

    df_persons = context.stage("synthesis.population.enriched")

    age_cat = pd.cut(df_persons["age"], bins=age_bins["bins"], labels=age_bins["labels"], right=False)
    df_persons["agecat"] = age_cat

    # assert df_persons["agecat"].isna().sum() == 0, "Some persons have no agecat: %s" % df_persons.loc[df_persons["agecat"].isna(), ["person_id", "age"]]

    df_motorcycles = df_persons[["person_id", "agecat", "sex"]].copy()

    df_motorcycles = df_motorcycles.rename(columns = { "person_id": "owner_id" })
    df_motorcycles["vehicle_id"] = df_motorcycles["owner_id"].astype(str) + ":motorcycle"
    df_motorcycles["type_id"] = "default_motorcycle"
    df_motorcycles["mode"] = "motorcycle"

    res = []

    with context.progress(label = "Processing motorcyles data ...", total = len(df_motorcycles)) as progress:
        with context.parallel(dict(fleet = df_motorcycles_fleet_counts), serialize=False) as parallel:
            for df_partial in parallel.imap(_sample_vehicle, df_motorcycles.to_dict(orient="records")):
                res.append(df_partial)

    df_motorcycles = pd.DataFrame.from_dict(res)

    return df_motorcycle_types, df_motorcycles