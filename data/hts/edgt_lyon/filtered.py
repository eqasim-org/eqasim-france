import data.hts.hts as hts
import numpy as np

"""
This stage filters out observations which live or work outside of the area.
"""

def configure(context):
    edgt_lyon_source = context.config("edgt_lyon_source", "unchosen")

    if edgt_lyon_source == "unchosen":
        raise RuntimeError("Using 'hts: edgt_lyon' without specifying 'edgt_lyon_source' (either 'cerema' or 'adisp')")
    elif edgt_lyon_source == "adisp":
        context.stage("data.hts.edgt_lyon.cleaned_adisp", alias="data.hts.edgt_lyon.cleaned")
    elif edgt_lyon_source == "cerema":
        context.stage("data.hts.edgt_lyon.cleaned_cerema", alias="data.hts.edgt_lyon.cleaned")
    else:
        raise RuntimeError("Unknown Lyon EDGT source (only 'cerema' and 'adisp' are supported): %s" % edgt_lyon_source)
    
    context.stage("data.spatial.codes")
    
    context.config("filter_hts",True)
def execute(context):
    filter_edgt = context.config("filter_hts")
    df_codes = context.stage("data.spatial.codes")
    df_households, df_persons, df_trips = context.stage("data.hts.edgt_lyon.cleaned")

    if filter_edgt : 
        # Filter for non-residents
        requested_departments = df_codes["departement_id"].unique()
        f = df_persons["departement_id"].astype(str).isin(requested_departments)
        df_persons = df_persons[f]

        # Filter for people going outside of the area
        remove_ids = set()

        remove_ids |= set(df_trips[
            ~df_trips["origin_departement_id"].astype(str).isin(requested_departments) | ~df_trips["destination_departement_id"].astype(str).isin(requested_departments)
        ]["person_id"].unique())

        df_persons = df_persons[~df_persons["person_id"].isin(remove_ids)]

        # Only keep trips and households that still have a person
        df_trips = df_trips[df_trips["person_id"].isin(df_persons["person_id"].unique())]
        df_households = df_households[df_households["household_id"].isin(df_persons["household_id"])]

    # Finish up
    df_households = df_households[hts.HOUSEHOLD_COLUMNS]
    df_persons = df_persons[hts.PERSON_COLUMNS]
    df_trips = df_trips[hts.TRIP_COLUMNS + ["routed_distance", "euclidean_distance"]]

    hts.check(df_households, df_persons, df_trips)
    return df_households, df_persons, df_trips
