import shapely.geometry as geo
import numpy as np
import pandas as pd
import geopandas as gpd

def configure(context):
    context.stage("data.spatial.municipalities")

    if context.config("education_location_source","bpe") == "addresses":
        context.stage("data.external.education", alias = "location_source")
    else:
        context.stage("data.bpe.cleaned", alias = "location_source")

EDUCATION_WEIGHT_MAP = [
    ("C101", 100),  # Preschools
    ("C102", 50),  # Intercommunal preschools
    ("C104", 145),  # Elemantary schools
    ("C105", 80),  # Intercommunal elemantary schools
    ("C301", 700),  # General and technological high schools, multi-purpose high schools
    ("C302", 285),  # Professional high schools
    ("C303", 100),  # Agricultural high schools
    ("C304", 30),  # General and technological classes in professional high schools
    ("C305", 30),  # Professional classes in general and technological high schools
    ("C403", 1000),  # Business schools
    ("C501", 2000),  # University
]

def fake_education(missing_communes, c, df_locations, df_zones):
    # Fake education destinations as the centroid of zones that have no other destinations
    print(
        "Adding fake education locations for %d municipalities"
        % (len(missing_communes))
    )

    df_added = []

    for commune_id in sorted(missing_communes):
        centroid = df_zones[df_zones["commune_id"] == commune_id][
            "geometry"
        ].centroid.iloc[0]

        df_added.append({"commune_id": commune_id, "geometry": centroid})

    df_added = gpd.GeoDataFrame(
        pd.DataFrame.from_records(df_added), crs=df_locations.crs
    )
    df_added["fake"] = True
    df_added["education_type"] = c
    df_added["weight"] = 1

    return df_added

def execute(context):
    df_locations = context.stage("location_source")

    df_locations = df_locations[df_locations["activity_type"] == "education"]
    df_locations = df_locations[["education_type", "commune_id","weight", "geometry"]].copy()
    df_locations["fake"] = False

    # Add education destinations to the centroid of zones that have no other destinations
    df_zones = context.stage("data.spatial.municipalities")

    required_communes = set(df_zones["commune_id"].unique())  
        
    if context.config("education_location_source") != 'bpe': # either weighted or addresses
        for prefix, weight in EDUCATION_WEIGHT_MAP:
            df_locations.loc[df_locations["education_type"]==prefix, "weight"] = (
                weight
            )  
    if context.config("education_location_source") != 'bpe' :

         
        # Add education destinations in function of level education
        for c in ["C1", "C2", "C3"]:
            missing_communes = required_communes - set(df_locations[df_locations["education_type"].str.startswith(c)]["commune_id"].unique())

            if len(missing_communes) > 0:
                df_locations = pd.concat([df_locations,fake_education(missing_communes, c, df_locations, df_zones)])
        
        # Add education destinations for last level education
        missing_communes = required_communes - set(df_locations[~(df_locations["education_type"].str.startswith(("C1", "C2", "C3")))]["commune_id"].unique())

        if len(missing_communes) > 0:

           df_locations = pd.concat([df_locations,fake_education(missing_communes, "C4", df_locations, df_zones)])
    else :

        missing_communes = required_communes - set(df_locations["commune_id"].unique())
        if len(missing_communes) > 0:

            df_locations = pd.concat([df_locations,fake_education(missing_communes, "C0", df_locations, df_zones)])
    df_locations["education_type"] = df_locations["education_type"].str[:2].astype("category")

    # Define identifiers
    df_locations["location_id"]= np.arange(len(df_locations))
    df_locations["location_id"] = "edu_" + df_locations["location_id"].astype(str)
    
    return df_locations[["location_id","education_type", "commune_id","weight","fake", "geometry"]]
