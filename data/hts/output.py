import pandas as pd
import tqdm
import numpy as np
import geopandas as gpd

"""
Often, we need the HTS for additioinal analyses, for instance, for the calibration
of mode shares. This stage makes it easy to extract the cleaned HTS from the
pipeline.
"""


def configure(context):
    context.stage("data.hts.selected")

    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")


def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.selected")

    df_households.to_csv(
        "%s/%shts_households.csv"
        % (context.config("output_path"), context.config("output_prefix")),
        sep=";",
        index=False,
    )

    df_persons.to_csv(
        "%s/%shts_persons.csv"
        % (context.config("output_path"), context.config("output_prefix")),
        sep=";",
        index=False,
    )

    df_trips.to_csv(
        "%s/%shts_trips.csv"
        % (context.config("output_path"), context.config("output_prefix")),
        sep=";",
        index=False,
    )
