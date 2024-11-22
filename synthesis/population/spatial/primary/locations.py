import numpy as np
import pandas as pd
import geopandas as gpd
from .candidates import EDUCATION_MAPPING

def configure(context):
    context.stage("synthesis.population.spatial.primary.candidates")
    context.stage("synthesis.population.spatial.commute_distance")
    context.stage("synthesis.population.spatial.home.locations")
    context.stage("synthesis.locations.work")
    context.stage("synthesis.locations.education")

    context.config("education_location_source", "bpe")


def define_distance_ordering(df_persons, df_candidates, progress):
    indices = []

    f_available = np.ones((len(df_candidates),), dtype = bool)
    costs = np.ones((len(df_candidates),)) * np.inf

    commute_coordinates = np.vstack([
        df_candidates["geometry"].x.values,
        df_candidates["geometry"].y.values
    ]).T

    for home_coordinate, commute_distance in zip(df_persons["home_location"], df_persons["commute_distance"]):
        home_coordinate = np.array([home_coordinate.x, home_coordinate.y])
        distances = np.sqrt(np.sum((commute_coordinates[f_available] - home_coordinate)**2, axis = 1))
        costs[f_available] = np.abs(distances - commute_distance)

        selected_index = np.argmin(costs)
        indices.append(selected_index)
        f_available[selected_index] = False
        costs[selected_index] = np.inf

        progress.update()

    assert len(set(indices)) == len(df_candidates)

    return indices

def define_random_ordering(df_persons, df_candidates, progress):
    progress.update(len(df_candidates))
    return np.arange(len(df_candidates))

define_ordering = define_distance_ordering

def process_municipality(context, origin_id):
    # Load data
    df_candidates, df_persons = context.data("df_candidates"), context.data("df_persons")

    # Find relevant records
    df_persons = df_persons[df_persons["commune_id"] == origin_id][[
        "person_id", "home_location", "commute_distance"
    ]].copy()
    df_candidates = df_candidates[df_candidates["origin_id"] == origin_id]

    # From previous step, this should be equal!
    assert len(df_persons) == len(df_candidates)

    indices = define_ordering(df_persons, df_candidates, context.progress)
    df_candidates = df_candidates.iloc[indices]

    df_candidates["person_id"] = df_persons["person_id"].values
    df_candidates = df_candidates.rename(columns = dict(destination_id = "commune_id"))

    return df_candidates[["person_id", "commune_id", "location_id", "geometry"]]

def process(context, purpose, df_persons, df_candidates):
    unique_ids = df_candidates["origin_id"].unique()

    df_result = []

    with context.progress(label = "Distributing %s destinations" % purpose, total = len(df_persons)) as progress:
        with context.parallel(dict(df_persons = df_persons, df_candidates = df_candidates)) as parallel:
            for df_partial in parallel.imap_unordered(process_municipality, unique_ids):
                df_result.append(df_partial)

    return pd.concat(df_result).sort_index()

def execute(context):
    data = context.stage("synthesis.population.spatial.primary.candidates")
    df_persons = data["persons"]

    # Separate data set
    df_work = df_persons[df_persons["has_work_trip"]]
    df_education = df_persons[df_persons["has_education_trip"]]

    # Attach home locations
    df_home = context.stage("synthesis.population.spatial.home.locations")

    df_work = pd.merge(df_work, df_home[["household_id", "geometry"]].rename(columns = {
        "geometry": "home_location"
    }), how = "left", on = "household_id")

    df_education = pd.merge(df_education, df_home[["household_id", "geometry"]].rename(columns = {
        "geometry": "home_location"
    }), how = "left", on = "household_id")

    # Attach commute distances
    df_commute_distance = context.stage("synthesis.population.spatial.commute_distance")

    df_work = pd.merge(df_work, df_commute_distance["work"], how = "left", on = "person_id")
    df_education = pd.merge(df_education, df_commute_distance["education"], how = "left", on = "person_id")

    # Attach geometry
    df_locations = context.stage("synthesis.locations.work")[["location_id", "geometry"]]
    df_work_candidates = data["work_candidates"]
    df_work_candidates = pd.merge(df_work_candidates, df_locations, how = "left", on = "location_id")
    df_work_candidates = gpd.GeoDataFrame(df_work_candidates)

    df_locations = context.stage("synthesis.locations.education")[["education_type", "location_id", "geometry"]]
    df_education_candidates = data["education_candidates"]
    df_education_candidates = pd.merge(df_education_candidates, df_locations, how = "left", on = "location_id")
    df_education_candidates = gpd.GeoDataFrame(df_education_candidates)

    # Assign destinations
    df_work = process(context, "work", df_work, df_work_candidates)
    if context.config("education_location_source") == 'bpe':
        df_education = process(context, "education", df_education, df_education_candidates)
    else :
        education = []
        for prefix, education_type in EDUCATION_MAPPING.items():
            education.append(process(context, prefix,df_education[df_education["age_range"]==prefix],df_education_candidates[df_education_candidates["education_type"].isin(education_type)]))
        df_education = pd.concat(education).sort_index()
    return df_work, df_education
