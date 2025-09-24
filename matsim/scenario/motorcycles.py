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
    context.stage("data.motorcycles.raw")

def _sample_vehicle(context, args):
    person = args
    df_counts = context.data("fleet")

    fleet = df_counts.loc[(df_counts["AGECAT"] == person["AGECAT"]) & (df_counts["SEXE"] == person["SEXE"])]

    vehicle = {}
    vehicle["vehicle_id"] = "m_%d" % person["person_id"]
    choice = fleet.sample(weights="POIDSVEHICULE") # TODO : rename POIDSVEHICULE to 'weight'

    pf = choice["PF"].values[0]
    age = choice["AGEVEHICULE"].values[0]

    vehicle["critair"] = "unknown"
    vehicle["technology"] = "petrol"
    vehicle["age"] = age
    vehicle["eudo"] = "unknown"

    # TODO : use hbefa categories
    vehicle["type_id"] = "default_motorcycle"

    return vehicle

def execute(context):

    df_persons = context.stage("synthesis.population.enriched")

    # df_homes might be usefull later so keeping it here for now
    # df_homes = context.stage("synthesis.population.spatial.home.zones")

    df_persons = df_persons.loc[df_persons["motorcycle_availability"] != "none"]
    df_persons = df_persons.loc[df_persons["age"] >= 14] # should not happen ... but it does

    df_persons = df_persons[["household_id", "person_id", "age", "sex"]]

    bins = [0,14,18,25,35,50,70,110]
    labels = ["%d_%d" % (a,b) for a,b in zip(bins, bins[1:])]
    age_cat = pd.cut(df_persons["age"], bins=bins, labels=labels, right=False)
    df_persons["AGECAT"] = age_cat

    df_persons["SEXE"] = df_persons["sex"].map({'male': 1.0, 'female': 2.0})
    df_motorcycle_counts = context.stage("data.2rm.raw")

    res = []

    with context.progress(label = "Processing motorcycle data ...", total = len(df_persons)) as progress:
        with context.parallel(dict(fleet = df_motorcycle_counts)) as parallel:
            for df_partial in parallel.imap(_sample_vehicle, df_persons.to_dict(orient="records")):
                res.append(df_partial)
                progress.update()

    df_motorcycles = pd.DataFrame.from_dict(res)

    return df_motorcycles