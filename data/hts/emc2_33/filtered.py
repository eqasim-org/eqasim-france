import data.hts.hts as hts

"""
This stage filters out observations which live or work outside of the area.
"""

def configure(context):
    context.stage("data.hts.emc2_33.cleaned")
    context.stage("data.spatial.codes")
    context.config("filter_hts",True)

def execute(context):
    filter_emc2 = context.config("filter_hts")
    df_codes = context.stage("data.spatial.codes")
    df_households, df_persons, df_trips = context.stage("data.hts.emc2_33.cleaned")
    
    if filter_emc2:
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
    households_columns = hts.HOUSEHOLD_COLUMNS[:]
    
    if "urban_type" in df_households:
        households_columns.append("urban_type")
    
    df_households = df_households[households_columns]
    df_persons = df_persons[hts.PERSON_COLUMNS]
    df_trips = df_trips[hts.TRIP_COLUMNS + ["routed_distance", "euclidean_distance"]]

    hts.check(df_households, df_persons, df_trips)
    
    return df_households, df_persons, df_trips
