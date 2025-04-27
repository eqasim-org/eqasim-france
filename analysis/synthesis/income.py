import pandas as pd
import numpy as np
import geopandas as gpd

import analysis.bootstrapping as bs
import analysis.statistics as stats
import analysis.marginals as marginals

def configure(context):
    acquisition_sample_size = context.config("acquisition_sample_size")
    bs.configure(context, "synthesis.population.income.selected", acquisition_sample_size)

def execute(context):
    acquisition_sample_size = context.config("acquisition_sample_size")

    probabilities = np.linspace(0.0, 1.0, 20)
    quantiles = []

    with context.progress(label = "Processing commute data ...", total = acquisition_sample_size) as progress:
        for df_income in bs.get_stages(context, "synthesis.population.income.selected", acquisition_sample_size):
            income = 12 * df_income["household_income"] / df_income["consumption_units"]
            quantiles.append([income.quantile(p) for p in probabilities])
            progress.update()

    quantiles = np.array(quantiles)

    mean = np.mean(quantiles, axis = 0)
    min = np.min(quantiles, axis = 0)
    max = np.max(quantiles, axis = 0)

    return pd.DataFrame(dict(mean = mean, min = min, max = max, cdf = probabilities))
