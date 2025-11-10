from tqdm import tqdm
import itertools
import numpy as np
import pandas as pd
import numba

import data.hts.egt.cleaned
import data.hts.entd.cleaned

import multiprocessing as mp

"""
This stage attaches obervations from the household travel survey to the synthetic
population sample. This is done by statistical matching.
"""

INCOME_CLASS = {
    "egt": data.hts.egt.cleaned.calculate_income_class,
    "entd": data.hts.entd.cleaned.calculate_income_class,
}

DEFAULT_MATCHING_ATTRIBUTES = [
    "sex", "any_cars", "age_class", "socioprofessional_class",
    "departement_id"
]

def configure(context):
    context.config("processes")
    context.config("random_seed")
    context.config("matching_minimum_observations", 20)
    context.config("matching_attributes", DEFAULT_MATCHING_ATTRIBUTES)

    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.income.selected")

    hts = context.config("hts")
    context.stage("data.hts.selected", alias = "hts")

@numba.jit(nopython = True) # Already parallelized parallel = True)
def sample_indices(uniform, cdf, selected_indices):
    indices = np.arange(len(uniform))

    for i, u in enumerate(uniform):
        indices[i] = np.count_nonzero(cdf < u)

    return selected_indices[indices]

def statistical_matching(progress, df_source, source_identifier, weight, df_target, target_identifier, columns, random_seed = 0, minimum_observations = 0):
    random = np.random.RandomState(random_seed)

    # Reduce data frames
    df_source = df_source[[source_identifier, weight] + columns].copy()
    df_target = df_target[[target_identifier] + columns].copy()

    # Sort data frames
    df_source = df_source.sort_values(by = columns)
    df_target = df_target.sort_values(by = columns)

    # Find unique values for all columns
    unique_values = {}

    for column in columns:
        unique_values[column] = list(sorted(set(df_source[column].unique()) | set(df_target[column].unique())))

    # Generate filters for all columns and values
    source_filters, target_filters = {}, {}

    for column, column_unique_values in unique_values.items():
        source_filters[column] = [df_source[column].values == value for value in column_unique_values]
        target_filters[column] = [df_target[column].values == value for value in column_unique_values]

    # Define search order
    source_filters = [source_filters[column] for column in columns]
    target_filters = [target_filters[column] for column in columns]

    # Perform matching
    weights = df_source[weight].values
    assigned_indices = np.ones((len(df_target),), dtype = int) * -1
    unassigned_mask = np.ones((len(df_target),), dtype = bool)
    assigned_levels = np.ones((len(df_target),), dtype = int) * -1
    uniform = random.random_sample(size = (len(df_target),))

    column_indices = [np.arange(len(unique_values[column])) for column in columns]

    for level in range(1, len(column_indices) + 1)[::-1]:
        level_column_indices = column_indices[:level]

        if np.count_nonzero(unassigned_mask) > 0:
            for column_index in itertools.product(*level_column_indices):
                f_source = np.logical_and.reduce([source_filters[i][k] for i, k in enumerate(column_index)])
                f_target = np.logical_and.reduce([target_filters[i][k] for i, k in enumerate(column_index)] + [unassigned_mask])

                selected_indices = np.nonzero(f_source)[0]
                requested_samples = np.count_nonzero(f_target)

                if requested_samples == 0:
                    continue

                if len(selected_indices) < minimum_observations:
                    continue

                selected_weights = weights[f_source]
                cdf = np.cumsum(selected_weights)
                cdf /= cdf[-1]

                assigned_indices[f_target] = sample_indices(uniform[f_target], cdf, selected_indices)
                assigned_levels[f_target] = level
                unassigned_mask[f_target] = False

                progress.update(np.count_nonzero(f_target))

    # Randomly assign unmatched observations
    cdf = np.cumsum(weights)
    cdf /= cdf[-1]

    assigned_indices[unassigned_mask] = sample_indices(uniform[unassigned_mask], cdf, np.arange(len(weights)))
    assigned_levels[unassigned_mask] = 0

    progress.update(np.count_nonzero(unassigned_mask))

    if np.count_nonzero(unassigned_mask) > 0:
        raise RuntimeError("Some target observations could not be matched. Minimum observations configured too high?")

    assert np.count_nonzero(unassigned_mask) == 0
    assert np.count_nonzero(assigned_indices == -1) == 0

    # Write back indices
    df_target[source_identifier] = df_source[source_identifier].values[assigned_indices]
    df_target = df_target[[target_identifier, source_identifier]]

    return df_target, assigned_levels

def _run_parallel_statistical_matching(context, args):
    # Pass arguments
    df_target, random_seed = args

    # Pass data
    df_source = context.data("df_source")
    source_identifier = context.data("source_identifier")
    weight = context.data("weight")
    target_identifier = context.data("target_identifier")
    columns = context.data("columns")
    minimum_observations = context.data("minimum_observations")

    return statistical_matching(context.progress, df_source, source_identifier, weight, df_target, target_identifier, columns, random_seed, minimum_observations)

def parallel_statistical_matching(context, df_source, source_identifier, weight, df_target, target_identifier, columns, minimum_observations = 0):
    random_seed = context.config("random_seed")
    processes = context.config("processes")

    random = np.random.RandomState(random_seed)
    chunks = np.array_split(df_target, processes)

    with context.progress(label = "Statistical matching ...", total = len(df_target)):
        with context.parallel({
            "df_source": df_source, "source_identifier": source_identifier, "weight": weight,
            "target_identifier": target_identifier, "columns": columns,
            "minimum_observations": minimum_observations
        }) as parallel:
                random_seeds = random.randint(10000, size = len(chunks))
                results = parallel.map(_run_parallel_statistical_matching, zip(chunks, random_seeds))

                levels = np.hstack([r[1] for r in results])
                df_target = pd.concat([r[0] for r in results])

                return df_target, levels

def execute(context):
    hts = context.config("hts")

    # Load data
    df_source_households, df_source_persons, df_source_trips = context.stage("hts")
    df_source = pd.merge(df_source_persons, df_source_households)

    df_target = context.stage("synthesis.population.sampled")

    columns = context.config("matching_attributes")

    try:
        default_index = columns.index("*default*")
        columns[default_index:default_index + 1] = DEFAULT_MATCHING_ATTRIBUTES
    except ValueError: pass

    # Define matching attributes
    AGE_BOUNDARIES = [14, 29, 44, 59, 74, 1000]

    if "age_class" in columns:
        df_target["age_class"] = np.digitize(df_target["age"], AGE_BOUNDARIES, right = True)
        df_source["age_class"] = np.digitize(df_source["age"], AGE_BOUNDARIES, right = True)

    if "income_class" in columns:
        df_income = context.stage("synthesis.population.income.selected")[["household_id", "household_income"]]

        df_target = pd.merge(df_target, df_income)
        df_target["income_class"] = INCOME_CLASS[hts](df_target)

    if "any_cars" in columns:
        df_target["any_cars"] = df_target["number_of_cars"] > 0
        df_source["any_cars"] = df_source["number_of_cars"] > 0

    # Perform statistical matching
    df_source = df_source.rename(columns = { "person_id": "hts_id" })

    for column in columns:
        if not column in df_source:
            raise RuntimeError("Attribute not available in source (HTS) for matching: {}".format(column))

        if not column in df_target:
            raise RuntimeError("Attribute not available in target (census) for matching: {}".format(column))

    df_assignment, levels = parallel_statistical_matching(
        context,
        df_source, "hts_id", "person_weight",
        df_target, "person_id",
        columns,
        minimum_observations = context.config("matching_minimum_observations"))

    df_target = pd.merge(df_target, df_assignment, on = "person_id")
    assert len(df_target) == len(df_assignment)

    context.set_info("matched_counts", {
        count: np.count_nonzero(levels >= count) for count in range(len(columns) + 1)
    })

    for count in range(len(columns) + 1):
        print("%d matched levels:" % count, np.count_nonzero(levels >= count), "%.2f%%" % (100 * np.count_nonzero(levels >= count) / len(df_target),))

    return df_target[["person_id", "hts_id"]]
