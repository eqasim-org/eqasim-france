import data.hts.hts as hts
import numpy as np

"""
This stage filters out EGT observations which live or work outside of
Île-de-France.
"""

def configure(context):
    context.stage("data.hts.egt.cleaned")
    context.stage("data.spatial.codes")

    context.config("filter_hts",True)
def execute(context):
    filter_egt = context.config("filter_hts") 
    df_codes = context.stage("data.spatial.codes")

    df_households, df_persons, df_trips = context.stage("data.hts.egt.cleaned")

    if filter_egt : 
        # Filter for non-residents
        requested_departments = df_codes["departement_id"].unique()
        f = df_persons["departement_id"].astype(str).isin(requested_departments) # pandas bug!
        df_persons = df_persons[f]

        # Filter for people going outside of the area (because they have NaN distances)
        remove_ids = set()

        remove_ids |= set(df_trips[
            ~df_trips["origin_departement_id"].astype(str).isin(requested_departments) | ~df_trips["destination_departement_id"].astype(str).isin(requested_departments)
        ]["person_id"].unique())

        remove_ids |= set(df_persons[
            ~df_persons["departement_id"].isin(requested_departments)
        ])

        df_persons = df_persons[~df_persons["person_id"].isin(remove_ids)]

        # Only keep trips and households that still have a person
        df_trips = df_trips[df_trips["person_id"].isin(df_persons["person_id"].unique())]
        df_households = df_households[df_households["household_id"].isin(df_persons["household_id"])]

    # Finish up
    household_columns = hts.HOUSEHOLD_COLUMNS + ["income_class"] + ["egt_household_id"]
    df_households = df_households[household_columns]
    
    person_columns = hts.PERSON_COLUMNS + ["egt_household_id", "egt_person_id"]
    if "urban_type" in df_persons: person_columns.append("urban_type")
    df_persons = df_persons[person_columns]
    
    trip_columns = hts.TRIP_COLUMNS + ["euclidean_distance"] + ["egt_household_id", "egt_person_id", "egt_trip_id"]
    df_trips = df_trips[trip_columns]

    hts.check(df_households, df_persons, df_trips)

    return df_households, df_persons, df_trips
