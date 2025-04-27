import pandas as pd
import geopandas as gpd
import os

import plotly.express as px 
ANALYSIS_FOLDER = "compare_flow_volume"

SAMPLING_RATE = 0.05

def configure(context):

    if not context.config("analysis_from_file",False) :
        context.stage("synthesis.population.trips")
        context.stage("synthesis.population.spatial.locations")
        context.stage("synthesis.population.enriched")
    context.stage("data.spatial.departments")

    context.config("comparison_file_prefix",None)
    context.config("output_prefix", "ile_de_france_")
    context.config("output_formats", ["csv", "gpkg"])
    context.config("output_path")
    context.config("data_path")

def stat_grid(df_trips,df_locations,df_persons,df_grid):
    
    # Write spatial trips
    df_spatial = pd.merge(df_trips, df_locations[[
        "person_id", "activity_index", "geometry"
    ]].rename(columns = {
        "activity_index": "following_activity_index",
    }), how = "left", on = ["person_id", "following_activity_index"])
    df_spatial = pd.merge(df_spatial,df_persons,how = "left", on = ["person_id",])
    df_spatial = gpd.GeoDataFrame(df_spatial, crs = "EPSG:2154").to_crs("4326")

    df_stats = gpd.sjoin(df_grid,df_spatial,how="left")
    return df_stats[['id_carr_1km', 'geometry','person_id', 'following_purpose', 'household_id', 'age']]
def execute(context):
    
    figures = {
        "Yrs:0-10":{"min_age": 0, "max_age": 10,},
        "Yrs:11-14":{"min_age": 11, "max_age": 14,},
        "Yrs:15-18":{"min_age": 15, "max_age": 17,},
        "Yrs:18-25":{"min_age": 18, "max_age": 25,},
        "Yrs:25-50":{"min_age": 26, "max_age": 50,},
        "Yrs:50-65":{"min_age": 51, "max_age": 65,},
        "Yrs:65-75":{"min_age": 66, "max_age": 75,},
        "Yrs:75+":{"min_age": 76, "max_age": 110,},}
    comparison_file = context.config("output_prefix") if context.config("comparison_file_prefix") is None else context.config("comparison_file_prefix")
    
    if not context.config("analysis_from_file"):
        print("Récupération simu données ...")
        # from simulation cache
        df_trips = context.stage("synthesis.population.trips")
        df_persons = context.stage("synthesis.population.enriched")[["person_id", "household_id","age"]]
        df_locations = context.stage("synthesis.population.spatial.locations")[[
            "person_id", "activity_index", "geometry"
        ]]
        df_trips["preceding_activity_index"] = df_trips["trip_index"]
        df_trips["following_activity_index"] = df_trips["trip_index"] + 1

    else :
        # from file trips, activites and person
        print("Récupération données ...")
        df_trips = pd.read_csv(f'{context.config("output_path")}/{context.config("output_prefix")}trips.csv',sep=';')[["person_id","trip_index" ,"following_activity_index","following_purpose"]]
        df_locations = gpd.read_parquet(f'{context.config("output_path")}/{context.config("output_prefix")}activities.geoparquet') if "geoparquet" in context.config("output_formats") else gpd.read_file(f'{context.config("output_path")}/{context.config("output_prefix")}activities.gpkg')
        df_persons = pd.read_csv(f'{context.config("output_path")}/{context.config("output_prefix")}persons.csv',sep=';')[["person_id", "household_id","age"]]  
    print("Récupération comp données ...")
    df_trips_comp = pd.read_csv(f'{context.config("output_path")}/{comparison_file}trips.csv',sep=';')[["person_id","trip_index" ,"following_activity_index","following_purpose"]]
    df_locations_comp = gpd.read_parquet(f'{context.config("output_path")}/{comparison_file}activities.geoparquet') if "geoparquet" in context.config("output_formats") else gpd.read_file(f'{context.config("output_path")}/{comparison_file}activities.gpkg')
    df_persons_comp = pd.read_csv(f'{context.config("output_path")}/{comparison_file}persons.csv',sep=';')[["person_id", "household_id","age"]]  
    
    list_purpose = list(df_trips["following_purpose"].unique())

    # grid 1km of location data
    df_departments = context.stage("data.spatial.departments")
    poly_dep = df_departments.unary_union
    df_grids = gpd.read_file(
            f'{context.config("data_path")}/grid/grille200m_metropole.gpkg',
            mask=poly_dep,
        )
    df_grids = df_grids.to_crs("4326")
    df_grid = df_grids[["id_carr_1km","geometry"]].dissolve(by="id_carr_1km").reset_index()

    df_stats = stat_grid(df_trips,df_locations,df_persons,df_grid)
    df_grids = stat_grid(df_trips_comp,df_locations_comp,df_persons_comp,df_grid)
    point = df_grid.unary_union.centroid # a changé avec ploy_dep
    print("Printing grids...")

    # check output folder existence
    analysis_output_path = os.path.join(context.config("output_path"), ANALYSIS_FOLDER)
    if not os.path.exists(analysis_output_path):
        os.mkdir(analysis_output_path)    

    for prefix, figure in figures.items():
        df_select_age = df_stats[df_stats["age"].between(figure["min_age"],figure["max_age"])]
        df_select_age = df_select_age.dissolve(by=["id_carr_1km","following_purpose"],aggfunc="count").reset_index()
        df_select_age = df_select_age[~(df_select_age["geometry"].isna())]
        df_select_age["following_purpose"] = df_select_age["following_purpose"].astype('str')

        df_grids_age = df_grids[df_grids["age"].between(figure["min_age"],figure["max_age"])]
        df_grids_age = df_grids_age.dissolve(by=["id_carr_1km","following_purpose"],aggfunc="count").reset_index()
        df_grids_age = df_grids_age[~(df_grids_age["geometry"].isna())]
        df_grids_age["following_purpose"] = df_grids_age["following_purpose"].astype('str')

        for purpose in list_purpose :
            df_select = df_select_age[df_select_age["following_purpose"]==purpose].rename(columns={"person_id":"count"})
            df_grids_select = df_grids_age[df_grids_age["following_purpose"]==purpose].rename(columns={"person_id":"count"})
            if context.config("output_prefix") == comparison_file :
                df_select = gpd.sjoin(df_select,df_grid,how='right',predicate="contains").fillna(0)
                df_select  = df_select[df_select["count"] != 0]
                fig = px.choropleth_mapbox(df_select,geojson=df_select.geometry,locations=df_select.index,color="count", opacity= 0.7,color_continuous_scale='reds',
                                        mapbox_style = 'open-street-map',center=dict(lat= point.y,lon=point.x),title=f"Localisation flow distribution for {prefix} group with {purpose} purpose")
                fig.write_html(f'{analysis_output_path}/{context.config("output_prefix")}{prefix}_{purpose}.html')
            else :
                df_grids_select = gpd.sjoin(df_grids_select,df_grid,how='right',predicate="contains").fillna(0)
                df_select = gpd.sjoin(df_select,df_grids_select.drop(columns=[ 'index_left']),how='right',predicate="contains").rename(columns={"count_left":"volume_studied_simu","count_right":"volume_compared_simu"}).fillna(0)
                df_select["volume_difference"] = df_select["volume_studied_simu"] - df_select["volume_compared_simu"]
                df_select  = df_select[(df_select["volume_studied_simu"] != 0 )| (df_select["volume_compared_simu"] != 0)]
                df_select["pourcentage_vol"] = df_select["volume_difference"] / df_select["volume_compared_simu"]
                px.choropleth_mapbox(df_select,geojson=df_select.geometry,locations=df_select.index,color="volume_difference", opacity= 0.7,color_continuous_scale="picnic", color_continuous_midpoint= 0,hover_name="id_carr_1km_right", hover_data=["volume_studied_simu", "volume_compared_simu","pourcentage_vol"],
                                        mapbox_style = 'open-street-map',center=dict(lat= point.y,lon=point.x),title=f"Comparison flow distribution with previous simulation for {prefix} group with {purpose} purpose").write_html(f'{analysis_output_path}/{context.config("output_prefix")}{prefix}_{purpose}.html')

            