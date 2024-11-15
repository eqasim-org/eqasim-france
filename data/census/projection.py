import pandas as pd
import os

"""
This stage loads and cleans projection data about the French population.
"""


def configure(context):
    context.config("data_path")
    context.config("projection_path", "projection_2021")
    context.config("projection_scenario", "00_central")
    context.config("projection_year", None)


def execute(context):
    source_path = "{}/{}/{}.xlsx".format(
        context.config("data_path"),
        context.config("projection_path"),
        context.config("projection_scenario"),
    )

    projection_year = int(context.config("projection_year"))

    df_all = pd.read_excel(source_path, sheet_name="population", skiprows=1).iloc[:107]

    df_male = pd.read_excel(source_path, sheet_name="populationH", skiprows=1).iloc[
        :107
    ]

    df_female = pd.read_excel(source_path, sheet_name="populationF", skiprows=1).iloc[
        :107
    ]

    df_male["sex"] = "male"
    df_female["sex"] = "female"

    assert df_all["Âge au 1er janvier"].iloc[-1] == "Total"
    assert df_male["Âge au 1er janvier"].iloc[-1] == "Total des hommes"
    assert df_female["Âge au 1er janvier"].iloc[-1] == "Total des femmes"

    df_sex = pd.concat([df_male.iloc[-1:], df_female.iloc[-1:]]).drop(
        columns=["Âge au 1er janvier"]
    )[["sex", projection_year]]
    df_sex.columns = ["sex", "projection"]

    df_age = df_all[["Âge au 1er janvier", projection_year]].iloc[:-1]
    df_age.columns = ["age", "projection"]

    df_male = df_male[["Âge au 1er janvier", "sex", projection_year]].iloc[:-1]
    df_female = df_female[["Âge au 1er janvier", "sex", projection_year]].iloc[:-1]

    df_male.columns = ["age", "sex", "projection"]
    df_female.columns = ["age", "sex", "projection"]

    df_cross = pd.concat([df_male, df_female])
    df_cross["sex"] = df_cross["sex"].astype("category")

    df_total = df_all.iloc[-1:].drop(columns=["Âge au 1er janvier"])[[projection_year]]
    df_total.columns = ["projection"]

    return {"total": df_total, "sex": df_sex, "age": df_age, "cross": df_cross}


def validate(context):
    if context.config("projection_year") is not None:
        source_path = "{}/{}/{}.xlsx".format(
            context.config("data_path"),
            context.config("projection_path"),
            context.config("projection_scenario"),
        )

        if not os.path.exists(source_path):
            raise RuntimeError("Projection data is not available")

        return os.path.getsize(source_path)

    return 0
