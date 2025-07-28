import os
import pandas as pd
import polars as pl
import zipfile

"""
Loads aggregate population data.
"""

def configure(context):
    context.config("data_path")
    context.stage("data.spatial.codes")
    context.config("population_path", "rp_2019/base-ic-evol-struct-pop-2019.zip")
    context.config("population_xlsx", "base-ic-evol-struct-pop-2019.xlsx")
    context.config("population_year", 19)

def execute(context):
    year = str(context.config("population_year"))

    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("population_path"))) as archive:
        with archive.open(context.config("population_xlsx")) as f:
            df_population = pl.read_excel(
                f.read(),
                sheet_name="IRIS",
                columns=["IRIS", "COM", "DEP", "REG", "P%s_POP" % year],
                read_options={"header_row": 5},
                schema_overrides={
                    "IRIS": pl.String,
                    "COM": pl.String,
                    "DEP": pl.String,
                    "REG": pl.Int32,
                },
            ).rename({
                "IRIS": "iris_id",
                "COM": "commune_id",
                "DEP": "departement_id",
                "REG": "region_id",
                "P%s_POP" % year: "population",
            })

    df_population = df_population.with_columns(
        pl.col("iris_id").cast(pl.Categorical),
        pl.col("commune_id").cast(pl.Categorical),
        pl.col("departement_id").cast(pl.Categorical),
    )

    # Merge into code data and verify integrity
    df_codes = context.stage("data.spatial.codes")
    df_population = pd.merge(
        df_population.to_pandas(),
        df_codes,
        on=["iris_id", "commune_id", "departement_id", "region_id"],
    )

    requested_iris = set(df_codes["iris_id"].unique())
    merged_iris = set(df_population["iris_id"].unique())

    if requested_iris != merged_iris:
        raise RuntimeError("Some IRIS are missing: %s" % (requested_iris - merged_iris,))

    return df_population[["region_id", "departement_id", "commune_id", "iris_id", "population"]]

def validate(context):
    if not os.path.exists("{}/{}".format(context.config("data_path"), context.config("population_path"))):
        raise RuntimeError("Aggregated census data is not available")

    return os.path.getsize("{}/{}".format(context.config("data_path"), context.config("population_path")))
     
