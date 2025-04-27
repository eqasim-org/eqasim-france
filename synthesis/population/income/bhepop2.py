import numpy as np
import pandas as pd
from synthesis.population.income.utils import income_uniform_sample, MAXIMUM_INCOME_FACTOR
from bhepop2.tools import add_household_size_attribute, add_household_type_attribute
from bhepop2.sources.marginal_distributions import QuantitativeMarginalDistributions
from bhepop2.enrichment.bhepop2 import Bhepop2Enrichment
from bhepop2.utils import PopulationValidationError, SourceValidationError

"""
This stage assigns a household income to each household of the synthesized
population, using the method Bhepop2 described in the package of the same name.
This method uses and fits the per-attribute distributions of Filosofi.
"""

INCOME_COLUMN = "income"


def configure(context):
    context.stage("data.income.municipality")
    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.spatial.home.zones")

    context.config("random_seed")


def _sample_income(context, args):
    commune_id, random_seed = args
    df_households, df_income = context.data("households"), context.data("income")

    random = np.random.RandomState(random_seed)

    # selection of commune population and distributions
    f = df_households["commune_id"] == commune_id
    df_selected = df_households[f].reset_index(drop=True)
    distribs = df_income[df_income["commune_id"] == commune_id]
    distribs = distribs.rename(
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

    try:
        # create source class from marginal distributions
        source = QuantitativeMarginalDistributions(
            distribs,
            "Filosofi",
            attribute_selection=[
                "size",  # modalities: ["1_pers", "2_pers", "3_pers", "4_pers", "5_pers_or_more"]
                "family_comp"  # modalities: ["Single_man", "Single_wom", "Couple_without_child", "Couple_with_child", "Single_parent", "complex_hh"]
            ],
            abs_minimum=0,
            relative_maximum=MAXIMUM_INCOME_FACTOR,
            delta_min=1000
        )

        # create enrichment class
        enrich_class = Bhepop2Enrichment(df_selected, source, feature_name=INCOME_COLUMN, seed=random_seed)

        # evaluate feature values on the population
        pop = enrich_class.assign_feature_values()

        # convert to monthly income
        pop[INCOME_COLUMN] = pop[INCOME_COLUMN] / 12
        pop[INCOME_COLUMN] = pop[INCOME_COLUMN].astype(int)
        incomes = pop[INCOME_COLUMN].values

        # print(f"Successfully enriched population on commune {commune_id} using bhepop2")
        context.progress.update(1)
        return f, incomes, "bhepop2"

    # if those exceptions are raised, it is likely that some distributions were missing
    except (PopulationValidationError, SourceValidationError, ValueError) as e:
        # print(f"Bhepop2 enrichment init on commune {commune_id} failed: {e}. Evaluate with original method.")

        # get global distribution of the commune
        distrib_all = distribs[distribs["modality"] == "all"]
        assert len(distrib_all) == 1
        centiles = list(distrib_all[["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]].iloc[0].values / 12)

        incomes = income_uniform_sample(random, centiles, len(df_selected))

        context.progress.update(1)
        return f, incomes, "uniform"


def execute(context):
    random = np.random.RandomState(context.config("random_seed"))

    # Load data
    df_income = context.stage("data.income.municipality")
    df_population = context.stage("synthesis.population.sampled")

    df_population = add_household_size_attribute(df_population)
    df_population = add_household_type_attribute(df_population)

    df_households = df_population[[
        "household_id", "consumption_units", "size", "family_comp"
    ]].drop_duplicates("household_id")

    df_homes = context.stage("synthesis.population.spatial.home.zones")[[
        "household_id", "commune_id"
    ]]

    df_households = pd.merge(df_households, df_homes)

    commune_ids = df_households["commune_id"].unique()
    random_seeds = random.randint(10000, size = len(commune_ids))

    # Perform sampling per commune
    with context.progress(label = "Imputing income ...", total = len(commune_ids)) as progress:
        with context.parallel(dict(households = df_households, income = df_income)) as parallel:

            for f, incomes, method in parallel.imap(_sample_income, zip(commune_ids, random_seeds)):
                df_households.loc[f, "household_income"] = incomes * df_households.loc[f, "consumption_units"]
                df_households.loc[f, "method"] = method

    # Cleanup
    df_households = df_households[["household_id", "household_income", "consumption_units"]]
    assert len(df_households) == len(df_households["household_id"].unique())

    return df_households
