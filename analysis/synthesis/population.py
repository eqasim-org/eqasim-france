
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from  analysis.marginals import NUMBER_OF_VEHICLES_LABELS
from shapely import distance
AGE_CLASS = [0, 10, 14, 17, 25, 50, 65, np.inf]
NUMBER_OF_VEHICLES= [0,1,2,3,np.inf]
NAME_AGE_CLASS = ["0-10","11-14","15-17","18-25","26-50","51-65","65+"]
ANALYSIS_FOLDER = "analysis_population"
def configure(context):

    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")
    context.config("sampling_rate")

    context.stage("synthesis.population.trips")
    context.stage("synthesis.population.enriched")
    context.stage("synthesis.population.spatial.locations")

    context.stage("data.census.filtered", alias = "census")
    context.stage("data.hts.selected", alias = "hts")

def execute(context):

    # check output folder existence
    analysis_output_path = os.path.join(context.config("output_path"), ANALYSIS_FOLDER)
    if not os.path.exists(analysis_output_path):
        os.mkdir(analysis_output_path)
    
    prefix = context.config("output_prefix")
    sampling_rate = context.config("sampling_rate")
    df_person_eq = context.stage("synthesis.population.enriched")
    df_trip_eq = context.stage("synthesis.population.trips")
    df_location_eq = context.stage("synthesis.population.spatial.locations")[["person_id", "activity_index", "geometry"]]
    
    df_location_eq = df_location_eq.to_crs("EPSG:2154")
    df_trip_eq["preceding_activity_index"] = df_trip_eq["trip_index"]
    df_trip_eq["following_activity_index"] = df_trip_eq["trip_index"] + 1
    
    df_census = context.stage("census")
    df_hts_households, df_hts_person, df_hts_trip = context.stage("hts")
    df_hts_person["person_weight"] *=df_census["weight"].sum()/df_hts_person["person_weight"].sum()
    df_hts_households["household_weight"] *=df_census["weight"].sum()/df_hts_households["household_weight"].sum()
    # get age class
    df_person_eq["age_class"] = pd.cut(df_person_eq["age"],AGE_CLASS,include_lowest=True,labels=NAME_AGE_CLASS)
    df_census["age_class"] = pd.cut(df_census["age"],AGE_CLASS,include_lowest=True,labels=NAME_AGE_CLASS)
    df_hts_person["age_class"] = pd.cut(df_hts_person["age"],AGE_CLASS,include_lowest=True,labels=NAME_AGE_CLASS)

    # get vehicule class 
    df_person_eq["vehicles_class"] = pd.cut(df_person_eq["number_of_vehicles"],NUMBER_OF_VEHICLES,right=True,labels=NUMBER_OF_VEHICLES_LABELS)
    df_hts_households["vehicles_class"] = pd.cut(df_hts_households["number_of_vehicles"],NUMBER_OF_VEHICLES,right=True,labels=NUMBER_OF_VEHICLES_LABELS)


    df_eq_travel = pd.merge(df_trip_eq,df_person_eq[["person_id","age_class"]],on=["person_id"])
    df_hts_travel = pd.merge(df_hts_trip,df_hts_person[["person_id","age_class","person_weight"]],on=["person_id"])

    print("Generate tables ...")
    # Age purpose analysis
    analysis_age_purpose = pd.pivot_table(df_eq_travel,"person_id",index="age_class",columns="following_purpose",aggfunc="count")
    analysis_age_purpose = analysis_age_purpose/sampling_rate
    analysis_age_purpose.to_csv(f"{analysis_output_path}/{prefix}age_purpose.csv")

    # Compare age volume
    analysis_age_class = pd.concat([df_census.groupby("age_class")["weight"].sum(),df_person_eq.groupby("age_class")["person_id"].count()],axis=1).reset_index()
    analysis_age_class.columns = ["Age class","INSEE","EQASIM"]
    analysis_age_class["Proportion_INSEE"] = analysis_age_class["INSEE"] /df_census["weight"].sum()
    analysis_age_class["Proportion_EQASIM"] = analysis_age_class["EQASIM"] /len(df_person_eq)
    analysis_age_class["EQASIM"] = analysis_age_class["EQASIM"]/sampling_rate
    analysis_age_class.to_csv(f"{analysis_output_path}/{prefix}age.csv")

    # Compare vehicle volume
    analysis_vehicles_class = pd.concat([df_hts_households.groupby("vehicles_class")["household_weight"].sum(),df_person_eq.groupby("vehicles_class")["household_id"].nunique()],axis=1).reset_index()
    analysis_vehicles_class.columns = ["Number of vehicles class","HTS","EQASIM"]
    analysis_vehicles_class["Proportion_HTS"] = analysis_vehicles_class["HTS"] / df_hts_households["household_weight"].sum() 
    analysis_vehicles_class["Proportion_EQASIM"] = analysis_vehicles_class["EQASIM"] / df_person_eq["household_id"].nunique() 
    analysis_vehicles_class.to_csv(f"{analysis_output_path}/{prefix}nbr_vehicle.csv")
    
    # Compare license volume 
    analysis_license_class = pd.concat([df_hts_person.groupby("has_license")["person_weight"].sum(),df_person_eq.groupby("has_license")["person_id"].count()],axis=1).reset_index()
    analysis_license_class.columns = ["Possession of license","HTS","EQASIM"]
    analysis_license_class["Proportion_HTS"] = analysis_license_class["HTS"] /df_hts_person["person_weight"].sum()
    analysis_license_class["Proportion_EQASIM"] = analysis_license_class["EQASIM"] /len(df_person_eq)
    analysis_license_class["EQASIM"] = analysis_license_class["EQASIM"]/sampling_rate
    analysis_license_class.to_csv(f"{analysis_output_path}/{prefix}license.csv")

    # Compare travel volume
    analysis_travel = pd.concat([df_hts_travel.groupby("age_class")["person_weight"].sum(),df_eq_travel.groupby("age_class")["person_id"].count()],axis=1).reset_index()
    analysis_travel.columns = ["Age class","HTS","EQASIM"]
    analysis_travel["Proportion_HTS"] = analysis_travel["HTS"] /df_hts_travel["person_weight"].sum()
    analysis_travel["Proportion_EQASIM"] = analysis_travel["EQASIM"] /len(df_eq_travel)
    analysis_travel["EQASIM"] = analysis_travel["EQASIM"]/sampling_rate
    analysis_travel.to_csv(f"{analysis_output_path}/{prefix}travel.csv")

    # Compare distance
    df_hts_travel["routed_distance"] = df_hts_travel["routed_distance"]/1000 if "routed_distance" in  df_hts_travel.columns else df_hts_travel["euclidean_distance"]/1000
    df_hts_travel["distance_class"] = pd.cut(df_hts_travel["routed_distance"],list(np.arange(100))+[np.inf])

    df_spatial = pd.merge(df_trip_eq, df_location_eq.rename(columns = {
        "activity_index": "preceding_activity_index",
        "geometry": "preceding_geometry"
    }), how = "left", on = ["person_id", "preceding_activity_index"])

    df_spatial = pd.merge(df_spatial, df_location_eq.rename(columns = {
        "activity_index": "following_activity_index",
        "geometry": "following_geometry"
    }), how = "left", on = ["person_id", "following_activity_index"])
    df_spatial["distance"] = df_spatial.apply(lambda x:distance( x["preceding_geometry"],x["following_geometry"])/1000,axis=1)
    df_spatial["distance_class"] = pd.cut(df_spatial["distance"],list(np.arange(100))+[np.inf])

    analysis_distance = pd.concat([df_hts_travel.groupby("distance_class")["person_weight"].sum(),df_spatial.groupby("distance_class")["person_id"].count()],axis=1).reset_index()
    analysis_distance.columns = ["Distance class","HTS","EQASIM"]
    analysis_distance["Proportion_HTS"] = analysis_distance["HTS"] / analysis_distance["HTS"].sum()
    analysis_distance["Proportion_EQASIM"] = analysis_distance["EQASIM"] / len(df_spatial)
    analysis_distance["EQASIM"] = analysis_distance["EQASIM"]/ sampling_rate
    analysis_distance.to_csv(f"{analysis_output_path}/{prefix}distance.csv")










