import pandas as pd
import numpy as np

"""
This stage reweights the census data set according to the projection data for a different year.
"""

def configure(context):
    context.stage("data.census.filtered")
    context.stage("synthesis.population.projection.ipu")

def execute(context):
    df_census = context.stage("data.census.filtered")
    df_weights = context.stage("synthesis.population.projection.ipu")

    initial_size = len(df_census)

    df_census = df_census.drop(columns = "weight")
    df_census = pd.merge(df_census, df_weights, on = "household_id")

    final_size = len(df_census)
    assert initial_size == final_size

    return df_census
