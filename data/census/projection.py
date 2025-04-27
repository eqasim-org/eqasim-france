import pandas as pd
import numpy as np

import os
import zipfile

from data.spatial.department_names import DEPARTMENTS

"""
This stage loads and cleans projection data about the French population.
"""

def configure(context):
    context.config("data_path")
    context.config("projection_path", "projections/donnees_detaillees_departementales.zip")
    context.config("projection_scenario", None)
    context.config("projection_year", None)

    context.stage("data.spatial.departments")

def execute(context):
    df_departments = context.stage("data.spatial.departments")

    # Reading data
    archive_path = "{}/{}".format(
        context.config("data_path"), 
        context.config("projection_path"))
    
    projection_year = int(context.config("projection_year"))
    projection_scenario = context.config("projection_scenario")

    with zipfile.ZipFile(archive_path) as archive:
        with archive.open("donnees_det_{}.xlsx".format(projection_scenario)) as f:
            df = pd.read_excel(f, sheet_name = "Population", skiprows = 5)

    # Clean sex
    df["sex"] = df["SEXE"].replace({ 1: "male", 2: "female" })

    # Clean age range
    df["minimum_age"] = df["TRAGE"].apply(lambda x: float(x.split(";")[0][1:]))
    df["maximum_age"] = df["TRAGE"].apply(lambda x: np.inf if "+" in x else float(x.split(";")[1][:-1]))
    
    # Clean department
    lookup = { name: identifier for identifier, name in DEPARTMENTS.items() }
    df["department_id"] = df["ZONE"].replace(lookup)

    requested_departments = set(df_departments["departement_id"])
    available_departments = set(df["department_id"])
    
    assert len(requested_departments - available_departments) == 0
    df = df[df["department_id"].isin(df_departments["departement_id"])]

    # Clean weight
    column = "POP_{}".format(projection_year)
    if not column in df:
        raise RuntimeError("Year {} is not available in projection data".format(projection_year))
    
    df["weight"] = df[column]

    # Cleanup
    df = df[["department_id", "sex", "minimum_age", "maximum_age", "weight"]] 
    return df

def validate(context):
    if context.config("projection_year") is not None or context.config("projection_scenario") is not None:
        source_path = "{}/{}".format(
            context.config("data_path"), 
            context.config("projection_path"))

        if not os.path.exists(source_path):
            raise RuntimeError("Projection data is not available")

        return os.path.getsize(source_path)
    
    return 0
