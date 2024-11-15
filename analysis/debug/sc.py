import numpy as np
import pandas as pd


def configure(context):
    context.stage("data.census.filtered", alias="census")
    context.stage("data.hts.selected", alias="hts")
    context.config("output_path")


def execute(context):
    df_census = context.stage("census")
    df_hts = context.stage("hts")[1]

    unique_values = set(df_census["socioprofessional_class"].unique())
    unique_values |= set(df_hts["socioprofessional_class"].unique())

    df_output = []

    for value in unique_values:
        f_census = df_census["socioprofessional_class"] == value
        f_hts = df_hts["socioprofessional_class"] == value

        df_output.append(
            {
                "value": value,
                "census_count": np.count_nonzero(f_census),
                "hts_count": np.count_nonzero(f_hts),
                "census_weight": df_census[f_census]["weight"].sum(),
                "hts_weight": df_hts[f_hts]["person_weight"].sum(),
            }
        )

    pd.DataFrame.from_records(df_output).to_csv(
        "{}/debug_sc.csv".format(context.config("output_path")), sep=";", index=False
    )
