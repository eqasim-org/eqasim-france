import numpy as np
import pandas as pd
from synthesis.population.income.utils import income_uniform_sample
import multiprocessing as mp
from tqdm import tqdm

"""
This stage assigns a household income to each household of the synthesized
population. For that it looks up the municipality of each household in the
income database to obtain the municipality's income distribution (in centiles).
Then, for each household, a centile is selected randomly from the respective
income distribution and a random income within the selected stratum is chosen.
"""

def configure(context):
    context.stage("data.income.municipality")
    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.spatial.home.zones")

    context.config("random_seed")


def _sample_income(context, args):
    commune_id, random_seed = args
    df_households, df_income = context.data("households"), context.data("income")

    random = np.random.RandomState(random_seed)

    f = df_households["commune_id"] == commune_id
    df_selected = df_households[f]

    centiles = list(df_income[df_income["commune_id"] == commune_id][["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9"]].iloc[0].values / 12)

    incomes = income_uniform_sample(random, centiles, len(df_selected))

    return f, incomes

def execute(context):
    random = np.random.RandomState(context.config("random_seed"))

    # Load data
    df_income = context.stage("data.income.municipality")
    df_income = df_income[(df_income["attribute"] == "all") & (df_income["value"] == "all")]

    df_households = context.stage("synthesis.population.sampled")[[
        "household_id", "consumption_units"
    ]].drop_duplicates("household_id")

    df_homes = context.stage("synthesis.population.spatial.home.zones")[[
        "household_id", "commune_id"
    ]]

    df_households = pd.merge(df_households, df_homes)

    # Perform sampling per commune
    with context.parallel(dict(households = df_households, income = df_income)) as parallel:
        commune_ids = df_households["commune_id"].unique()
        random_seeds = random.randint(10000, size = len(commune_ids))

        for f, incomes in context.progress(parallel.imap(_sample_income, zip(commune_ids, random_seeds)), label = "Imputing income ...", total = len(commune_ids)):
            df_households.loc[f, "household_income"] = incomes * df_households.loc[f, "consumption_units"]

    # Cleanup
    df_households = df_households[["household_id", "household_income", "consumption_units"]]
    assert len(df_households) == len(df_households["household_id"].unique())
    return df_households
