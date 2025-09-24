import pandas as pd
import os
import re

"""
This stage creates the various type of motorcycles needed for the simulation with HBEFA emissions
"""

def configure(context):
    pass

def _get_type_id(row):
    result = "motorcycle_"

    match row["hbefa_size"]:
        case "<=50cc":
            result += "lte_50cc_"
        case "<=250cc":
            result += "lte_250cc_"
        case ">250cc":
            result += "gt_250cc_"
        case _:
            pass

    if "v<30kmh" in row["Segment"]:
        result += "30kmh_"
    elif "v<50kmh" in row["Segment"]:
        result += "50kmh_"

    if "2S <=250cc" in row["Segment"]:
        result += "2S_"
    if "4S <=250cc" in row["Segment"]:
        result += "4S_"
    if "4S >250cc" in row["Segment"]:
        result += "4S_"

    if "Electric" in row["hbefa_emission"]:
        result += "electric"

    if res := re.search(r"(Euro[\s-]?|EU)(\d+)", row["hbefa_emission"]):
        result += f"euro_{res.group(2)}"

    return result

def execute(context):

    default_motorcycle_type = {
        'type_id': 'default_motorcycle', 'nb_seats': 1, 'length': 2.0, 'width': 1.0, 'pce': 1.0, 'mode': "motorcycle",
        'hbefa_cat': "motorcycle", 'hbefa_tech': "average", 'hbefa_size': "average", 'hbefa_emission': "average",
    }

    csv_path = os.path.join(os.path.dirname(__file__), "motocycles_hbefa_subsegments.csv")
    df_types = pd.read_csv(csv_path, sep=";")

    df_types["nb_seats"] = 1
    df_types["length"] = 2.0
    df_types["width"] = 1.0
    df_types["pce"] = 1.0
    df_types["mode"] = "motorcycle"
    df_types["hbefa_cat"] = "motorcycle"

    df_types.rename(columns={
        "Technology": "hbefa_tech",
        "SizeClass": "hbefa_size",
        "EmissionConcept(aggreg)": "hbefa_emission",
    }, inplace=True)

    df_types["type_id"] = df_types.apply(_get_type_id, axis=1)

    df_types = df_types[[
        "type_id", "nb_seats", "length", "width", "pce", "mode",
        "hbefa_cat", "hbefa_tech", "hbefa_size", "hbefa_emission",
    ]]
    df_types = df_types.drop_duplicates()
    
    # Add default_motorcycle_type to df_types
    df_types = pd.concat([df_types, pd.DataFrame([default_motorcycle_type])], ignore_index=True)

    assert df_types["type_id"].is_unique, "type_id is not unique"

    return df_types