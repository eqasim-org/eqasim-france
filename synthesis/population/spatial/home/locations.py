import data.spatial.utils as spatial_utils
import numpy as np
import pandas as pd
import geopandas as gpd

def configure(context):
    context.stage("synthesis.population.spatial.home.zones")
    context.stage("synthesis.locations.home.locations")
    context.config("home_location_source", "addresses")
    
    context.config("random_seed")
    context.config("use_housing_type", False)

def _sample_locations(context, args):
    # Extract data sets
    df_locations = context.data("df_locations")
    df_homes = context.data("df_homes")

    # Extract task parameters
    iris_id, random_seed = args

    # Select home candidates and locations for the selected IRIS
    df_homes = df_homes[df_homes["iris_id"] == iris_id].copy()
    df_locations = df_locations[df_locations["iris_id"] == iris_id].copy()

    # Verify counts
    home_count = len(df_homes)
    location_count = len(df_locations)

    assert location_count > 0
    assert home_count > 0

    # Perform sampling
    random = np.random.default_rng(random_seed)

    cdf = np.cumsum(df_locations["weight"].values)
    cdf /= cdf[-1]

    indices = np.array([np.count_nonzero(cdf < u) 
        for u in random.random(size = home_count)])

    if context.config("use_housing_type"):
        # we already have a basic random assignment
        # now we override it if desired
        assert "housing" in df_locations, "Home locations do not contain housing information. Are you using home_location_source = addresses?"

        for housing_type in ("single", "double", "collective"):
            f_homes = df_homes["housing_type"].eq(housing_type)

            if housing_type == "single":
                f_locations = df_locations["housing"].eq(1)
            elif housing_type == "double":
                f_locations = df_locations["housing"].eq(2)
            else:
                f_locations = df_locations["housing"].ge(3)

            home_count = np.count_nonzero(f_homes)
            location_count = np.count_nonzero(f_locations)

            home_selector = np.where(f_homes)[0]
            location_selector = np.where(f_locations)[0]

            if home_count > 0 and location_count > 0:
                cdf = np.cumsum(df_locations.loc[f_locations, "weight"].values)
                cdf /= cdf[-1]

                indices[home_selector] = location_selector[np.array([np.count_nonzero(cdf < u) 
                    for u in random.random(size = home_count)])]

    # Apply selection
    df_homes["geometry"] = df_locations.iloc[indices]["geometry"].values
    df_homes["location_id"] = df_locations.iloc[indices]["location_id"].values
    
    # Update progress
    context.progress.update()

    return gpd.GeoDataFrame(df_homes, crs = df_locations.crs)

def execute(context):
    random = np.random.default_rng(context.config("random_seed"))

    df_homes = context.stage("synthesis.population.spatial.home.zones")
    df_locations = context.stage("synthesis.locations.home.locations")
                   
    # Sample locations for home
    unique_iris_ids = sorted(set(df_homes["iris_id"].unique()))

    with context.progress(label = "Sampling home locations ...", total = len(unique_iris_ids)):
        with context.parallel(dict(
            df_locations = df_locations, df_homes = df_homes
        )) as parallel:
            seeds = random.integers(10000, size = len(unique_iris_ids))
            df_homes = pd.concat(parallel.map(_sample_locations, zip(unique_iris_ids, seeds)))
    out = ["household_id", "commune_id", "location_id", "geometry"]
        
    return df_homes[out]
