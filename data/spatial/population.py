import os
import pandas as pd
import zipfile

"""
Loads aggregate population data.
"""

def configure(context):
    context.config("data_path")
    context.stage("data.spatial.codes")
    context.config("population_path", "rp_2022/base-ic-evol-struct-pop-2022_csv.zip")
    context.config("population_csv", "base-ic-evol-struct-pop-2022.CSV")
    context.config("population_year", 22)

def execute(context):
    year = str(context.config("population_year"))

    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("population_path"))) as archive:
        with archive.open(context.config("population_csv")) as f:
            df_population = pd.read_csv(
                f,
                sep = ";",  usecols = ["IRIS", "COM", "P%s_POP" % year],dtype={"IRIS":str,"COM":str}
            ).rename(columns = {
                "IRIS": "iris_id", "COM": "commune_id",
                "P%s_POP" % year: "population"
            })

    df_population["iris_id"] = df_population["iris_id"].astype("category")  
    df_population["commune_id"] = df_population["commune_id"].astype("category")

    # Merge into code data and verify integrity
    df_codes = context.stage("data.spatial.codes")
    df_population = pd.merge(df_population, df_codes, on = ["iris_id", "commune_id"])

    requested_iris = set(df_codes["iris_id"].unique())
    merged_iris = set(df_population["iris_id"].unique())

    if requested_iris != merged_iris:
        raise RuntimeError("Some IRIS are missing: %s" % (requested_iris - merged_iris,))

    return df_population[["region_id", "departement_id", "commune_id", "iris_id", "population"]]

def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("population_path"))):
        raise RuntimeError("Aggregated census data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("population_path")))
     