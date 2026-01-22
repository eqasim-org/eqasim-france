import pandas as pd
import numpy as np

import analysis.bootstrapping as bs
import analysis.statistics as stats
import analysis.marginals as marginals

def configure(context):
    acquisition_sample_size = context.config("acquisition_sample_size")

    bs.configure(context, "synthesis.population.spatial.locations", acquisition_sample_size)
    bs.configure(context, "synthesis.population.trips", acquisition_sample_size)

def execute(context):
    acquisition_sample_size = context.config("acquisition_sample_size")

    probabilities = np.linspace(0.0, 1.0, 20)
    modes = ["car", "car_passenger", "pt", "bicycle", "walk"]

    quantiles = { mode : [] for mode in modes }

    generator = zip(
        bs.get_stages(context, "synthesis.population.spatial.locations", acquisition_sample_size),
        bs.get_stages(context, "synthesis.population.trips", acquisition_sample_size)
    )

    with context.progress(label = "Processing distance data ...", total = acquisition_sample_size) as progress:
        for df_locations, df_trips in generator:
            # Load locations and calculate euclidean distances
            df_locations = df_locations[["person_id", "activity_index", "geometry"]].rename(columns = { "activity_index": "trip_index" })
            df_locations["euclidean_distance"] = df_locations["geometry"].distance(df_locations["geometry"].shift(-1))

            # Merge mode into distances
            df_trips = pd.merge(
                df_trips[["person_id", "trip_index", "mode", "preceding_purpose", "following_purpose", "departure_time", "arrival_time"]],
                df_locations, on = ["person_id", "trip_index"], how = "inner"
            )
            df_trips["travel_time"] = df_trips["arrival_time"] - df_trips["departure_time"]

            # Filter trips
            primary_activities = ["home", "work", "education"]
            #primary_activities = []
            df_trips = df_trips[~(
                df_trips["preceding_purpose"].isin(primary_activities) &
                df_trips["following_purpose"].isin(primary_activities)
            )]

            # Calculate quantiles
            for mode in modes:
                df_mode = df_trips[df_trips["mode"] == mode]
                quantiles[mode].append([df_mode["euclidean_distance"].quantile(p) for p in probabilities])

            progress.update()

    for mode in modes:
        quantiles[mode] = np.array(quantiles[mode])

    df_data = []

    for mode in modes:
        mean = np.mean(quantiles[mode], axis = 0)
        #min = np.percentile(quantiles[mode], 5, axis = 0)
        #max = np.percentile(quantiles[mode], 95, axis = 0)

        min = np.min(quantiles[mode], axis = 0)
        max = np.max(quantiles[mode], axis = 0)

        df_data.append(pd.DataFrame(dict(mean = mean, min = min, max = max, cdf = probabilities)))
        df_data[-1]["mode"] = mode

    return pd.concat(df_data)
