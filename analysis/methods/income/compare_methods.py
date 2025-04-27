from synthesis.population.income.utils import MAXIMUM_INCOME_FACTOR
from bhepop2.tools import add_household_size_attribute, add_household_type_attribute
from bhepop2.sources.marginal_distributions import QuantitativeMarginalDistributions
import pandas as pd
import os

"""
Compare income assignation methods available in Eqasim.

Comparison is realised on the synthetic population of the most populated commune.
"""

COMPARE_INCOME_FOLDER = "compare_income_methods"


def configure(context):
    context.config("output_path")
    context.stage("data.income.municipality")
    context.stage("synthesis.population.income.uniform", alias="uniform")
    context.stage("synthesis.population.income.bhepop2", alias="bhepop2")
    context.stage("synthesis.population.sampled")


def execute(context):

    # get complete population (needed to add attributes)
    df_population = context.stage("synthesis.population.sampled")
    df_population = add_household_size_attribute(df_population)
    df_population = add_household_type_attribute(df_population)

    # get most populated commune
    commune_id = df_population.groupby(["commune_id"], observed=True)["commune_id"].count().drop("undefined").idxmax()

    # get income distributions by attributes
    income_df = context.stage("data.income.municipality").query(f"commune_id == '{commune_id}'")
    income_df = income_df.rename(
        columns={
            "value": "modality",
            "q1": "D1",
            "q2": "D2",
            "q3": "D3",
            "q4": "D4",
            "q5": "D5",
            "q6": "D6",
            "q7": "D7",
            "q8": "D8",
            "q9": "D9",
        }
    )

    households_with_attributes = df_population[[
        "household_id", "commune_id", "size", "family_comp"
    ]].drop_duplicates("household_id")

    # get enriched population with different methods
    uniform_pop_df = context.stage("uniform")
    uniform_pop_df = uniform_pop_df.merge(households_with_attributes, on="household_id")
    uniform_pop_df["household_income"] = (
            uniform_pop_df["household_income"] * 12 / uniform_pop_df["consumption_units"]
    )
    uniform_pop_df = uniform_pop_df.query(f"commune_id == '{commune_id}'")

    bhepop2_pop_df = context.stage("bhepop2")
    bhepop2_pop_df = bhepop2_pop_df.merge(households_with_attributes, on="household_id")
    bhepop2_pop_df["household_income"] = (
            bhepop2_pop_df["household_income"] * 12 / bhepop2_pop_df["consumption_units"]
    )
    bhepop2_pop_df = bhepop2_pop_df.query(f"commune_id == '{commune_id}'")

    # prepare populations analysis

    # create a source from the Filosofi distributions
    marginal_distributions_source = QuantitativeMarginalDistributions(
        income_df,
        "Filosofi",
        ["size", "family_comp"],
        0,
        relative_maximum=MAXIMUM_INCOME_FACTOR,
        delta_min=1000
    )

    # check output folder existence
    compare_output_path = os.path.join(context.config("output_path"), COMPARE_INCOME_FOLDER)
    if not os.path.exists(compare_output_path):
        os.mkdir(compare_output_path)

    # create an analysis instance
    analysis = marginal_distributions_source.compare_with_populations(
        {
            "Uniform": uniform_pop_df,
            "Bhepop2": bhepop2_pop_df
        },
        feature_name="household_income",
        output_folder=compare_output_path
    )
    analysis.plot_title_format = analysis.plot_title_format + f" \n(commune={commune_id})"

    analysis.generate_analysis_plots()
    analysis.generate_analysis_error_table()

    print(f"Generated compared analysis of income assignation methods in {compare_output_path}")


