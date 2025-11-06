import numpy as np
import pandas as pd

DISTANCE_CLASS_BOUNDS = [ 5000, 10000, 20000, 50000, np.inf]

def clean_work_commutes(df_data,df_distances):
    # calculate distance 
    df_data = pd.merge(df_data, df_distances, on = ["origin_id", "destination_id"]).rename(columns={"centroid_distance":"commute_distance"})
    #print(df_data[df_data["origin_id"]!=df_data["destination_id"]][["origin_id", "destination_id","commute_distance"]].values[0])

    # get distance class
    df_data["distance_class"] = calculate_distance_class(df_data)
    # grouping data
    df_data = df_data.groupby(["origin_id","socioprofessional_class","distance_class"],as_index=False)["weight"].sum()
    return df_data


def calculate_distance_class(df):
    assert "commute_distance" in df

    return np.digitize(df["commute_distance"], DISTANCE_CLASS_BOUNDS, right = True)
