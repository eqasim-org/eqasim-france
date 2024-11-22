from tqdm import tqdm
import itertools
import numpy as np
import pandas as pd
import numba

import data.hts.egt.cleaned
import data.hts.entd.cleaned

import multiprocessing as mp

"""
This stage fuses census data with HTS data.
"""

def configure(context):
    context.stage("synthesis.population.matched")
    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.income.selected")

    hts = context.config("hts")
    context.stage("data.hts.selected", alias = "hts")

def execute(context):
    # Select population columns
    df_population = context.stage("synthesis.population.sampled")[[
        "person_id", "household_id",
        "census_person_id", "census_household_id",
        "age", "sex", "employed", "studies",
        "number_of_vehicles", "household_size", "consumption_units",
        "socioprofessional_class"
    ]]

    # Attach matching information
    df_matching = context.stage("synthesis.population.matched")
    df_population = pd.merge(df_population, df_matching, on = "person_id")

    initial_size = len(df_population)
    initial_person_ids = len(df_population["person_id"].unique())
    initial_household_ids = len(df_population["household_id"].unique())

    # Attach person and household attributes from HTS
    df_hts_households, df_hts_persons, _ = context.stage("hts")
    df_hts_persons = df_hts_persons.rename(columns = { "person_id": "hts_id", "household_id": "hts_household_id" })
    df_hts_households = df_hts_households.rename(columns = { "household_id": "hts_household_id" })

    df_population = pd.merge(df_population, df_hts_persons[[
        "hts_id", "hts_household_id", "has_license", "has_pt_subscription", "is_passenger"
    ]], on = "hts_id")

    df_population = pd.merge(df_population, df_hts_households[[
        "hts_household_id", "number_of_bikes"
    ]], on = "hts_household_id")

    # Attach income
    df_income = context.stage("synthesis.population.income.selected")
    df_population = pd.merge(df_population, df_income[[
        "household_id", "household_income"
    ]], on = "household_id")

    # Check consistency
    final_size = len(df_population)
    final_person_ids = len(df_population["person_id"].unique())
    final_household_ids = len(df_population["household_id"].unique())

    assert initial_size == final_size
    assert initial_person_ids == final_person_ids
    assert initial_household_ids == final_household_ids

    # Add car availability
    df_number_of_cars = df_population[["household_id", "number_of_vehicles"]].drop_duplicates("household_id")
    df_number_of_licenses = df_population[["household_id", "has_license"]].groupby("household_id").sum().reset_index().rename(columns = { "has_license": "number_of_licenses" })
    df_car_availability = pd.merge(df_number_of_cars, df_number_of_licenses)

    df_car_availability["car_availability"] = "all"
    df_car_availability.loc[df_car_availability["number_of_vehicles"] < df_car_availability["number_of_licenses"], "car_availability"] = "some"
    df_car_availability.loc[df_car_availability["number_of_vehicles"] == 0, "car_availability"] = "none"
    df_car_availability["car_availability"] = df_car_availability["car_availability"].astype("category")

    df_population = pd.merge(df_population, df_car_availability[["household_id", "car_availability"]])

    # Add bike availability
    df_population["bike_availability"] = "all"
    df_population.loc[df_population["number_of_bikes"] < df_population["household_size"], "bike_availability"] = "some"
    df_population.loc[df_population["number_of_bikes"] == 0, "bike_availability"] = "none"
    df_population["bike_availability"] = df_population["bike_availability"].astype("category")
    
    # Add age range for education
    df_population["age_range"] = "higher_education"
    df_population.loc[df_population["age"]<=10,"age_range"] = "primary_school"
    df_population.loc[df_population["age"].between(11,14),"age_range"] = "middle_school"
    df_population.loc[df_population["age"].between(15,17),"age_range"] = "high_school"
    df_population["age_range"] = df_population["age_range"].astype("category")
    
    return df_population
