import pandas as pd
import numpy as np


def configure(context):
    context.stage("data.od.cleaned")
    context.stage("data.spatial.centroid_distances")


def execute(context):
    df_distances = context.stage("data.spatial.centroid_distances")
    result = {}

    for df_data, name in zip(context.stage("data.od.cleaned"), ("work", "education")):
        df_data = pd.merge(df_data, df_distances, on=["origin_id", "destination_id"])

        df_data = df_data[["centroid_distance", "weight"]]
        df_data = df_data.sort_values(by="centroid_distance")
        df_data["cdf"] = np.cumsum(df_data["weight"])
        df_data["cdf"] /= df_data["cdf"].max()
        df_data = df_data[["centroid_distance", "cdf"]]

        result[name] = df_data

    return result
