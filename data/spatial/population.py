import os
import pandas as pd
import zipfile

"""
Loads aggregate population data.
"""

def configure(context):
    context.config("data_path")
    context.stage("data.spatial.codes")
    context.config("population_path", "rp_2021/base-ic-evol-struct-pop-2021_xlsx.zip")
    context.config("population_xlsx", "base-ic-evol-struct-pop-2021.xlsx")
    context.config("population_year", 21)

def execute(context):
    year = str(context.config("population_year"))

    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("population_path"))) as archive:
        with archive.open(context.config("population_xlsx")) as f:
            df_population = pd.read_excel(
                f,
                skiprows = 5, sheet_name = "IRIS", usecols = ["IRIS", "COM", "DEP", "REG", "P%s_POP" % year]
            ).rename(columns = {
                "IRIS": "iris_id", "COM": "commune_id", "DEP": "departement_id", "REG": "region_id",
                "P%s_POP" % year: "population"
            })

    df_population["iris_id"] = df_population["iris_id"].astype("category")
    df_population["commune_id"] = df_population["commune_id"].astype("category")
    df_population["departement_id"] = df_population["departement_id"].astype("category")
    df_population["region_id"] = df_population["region_id"].astype(int)

    # Merge into code data and verify integrity
    df_codes = context.stage("data.spatial.codes")
    df_population = pd.merge(df_population, df_codes, on = ["iris_id", "commune_id", "departement_id", "region_id"])

    requested_iris = set(df_codes["iris_id"].unique())
    merged_iris = set(df_population["iris_id"].unique())

    if requested_iris != merged_iris:
        raise RuntimeError("Some IRIS are missing: %s" % (requested_iris - merged_iris,))

    return df_population[["region_id", "departement_id", "commune_id", "iris_id", "population"]]

def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("population_path"))):
        raise RuntimeError("Aggregated census data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("population_path")))
     