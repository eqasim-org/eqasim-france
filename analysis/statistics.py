import itertools
import numba

import numpy as np
import pandas as pd


@numba.jit(nopython=True, parallel=True)
def _combine_filter(filters):
    return np.logical_and.reduce(filters)


def marginalize(df, marginals, weight_column="weight", count_column="weight"):
    """
    This function takes a data frame and a list of marginals in the form

        [("column1", "column2"), ("column3",), tuple()]

    i.e. there can be multi-dimensional marginals. An empty tuple represents
    the total weight of the population. The weight for each observation is given
    through the weight_column parameter. It can be None if the data frame is not
    weighted.

    The output is a dictionary with marginals as keys and data frames as values
    with the shape ("column1", "column2", ..., "weight")
    """

    assert weight_column in df or weight_column is None
    assert not count_column in df or weight_column == count_column

    # Find unique columns that are involved to speed up process
    unique_columns = set()

    for marginal in marginals:
        unique_columns |= set(marginal)

    unique_columns = list(unique_columns)

    # Find values of all unique columns
    unique_values = {}

    for column in unique_columns:
        assert column in df
        unique_values[column] = df[column].unique()

    # Find filters for all values in all columns
    filters = {}

    for column in unique_columns:
        column_filters = []
        filters[column] = column_filters

        for value in unique_values[column]:
            column_filters.append((df[column] == value).values)

    # Set up numpy weights
    weights = np.ones((len(df),)) if weight_column is None else df[weight_column].values

    # Go through all marginals and create a table per marginals
    results = {}

    for columns in marginals:
        if len(columns) == 0:  # Total is requested
            total = len(df) if weight_column is None else df[weight_column].sum()
            results[columns] = pd.DataFrame.from_records(
                [["value", total]], columns=["total", count_column]
            )
        else:
            marginal_records = []
            value_index_lists = [
                np.arange(len(unique_values[column])) for column in columns
            ]

            for value_indices in itertools.product(*value_index_lists):
                marginal_values = [
                    unique_values[column][value_index]
                    for column, value_index in zip(columns, value_indices)
                ]
                marginal_filters = [
                    filters[column][value_index]
                    for column, value_index in zip(columns, value_indices)
                ]
                f = np.logical_and.reduce(marginal_filters)

                if weight_column is None:
                    marginal_count = np.count_nonzero(f)
                else:
                    marginal_count = weights[f].sum()

                marginal_records.append(marginal_values + [marginal_count])

            marginal_records = pd.DataFrame.from_records(
                marginal_records, columns=list(columns) + [count_column]
            )
            results[columns] = marginal_records

    return results


def apply_per_marginal(marginals, f):
    return {marginal: f(df) for marginal, df in marginals.items()}


def collect_sample(dfs, column="realization"):
    """
    This function combines multiple structurally equal data frames into one
    by adding an additional column denoting the number of the realization.
    """
    assert len(dfs) > 0
    assert not column in dfs[0]

    first_columns = list(dfs[0].columns)
    new_dfs = []

    for index, df in enumerate(dfs):
        assert list(df.columns) == first_columns

        new_df = df.copy()
        new_df[column] = index
        new_dfs.append(new_df)

    return pd.concat(new_dfs)


def combine_marginals(realizations, column="realization"):
    """
    This function combines multiple realizations of the "marginalize" output into
    a new data structure that is equivalent to the one of "marginalize", but with
    an additional column for each marginal denoting the realization.
    """
    assert len(realizations) > 0

    marginals = realizations[0].keys()
    marginal_columns = {
        marginal: list(realizations[0][marginal].columns) for marginal in marginals
    }

    # Check that all realizations have the same structure as the first
    for realization in realizations:
        assert len(marginals - realization.keys()) == 0

        for marginal in marginals:
            assert list(realization[marginal].columns) == marginal_columns[marginal]

    # Go through all marginals and collect the samples
    sample = {}

    for marginal in marginals:
        sample[marginal] = collect_sample(
            [realization[marginal] for realization in realizations], column
        )

    return sample


def bootstrap(
    df,
    bootstrap_size,
    random,
    realization_column="realization",
    bootstrap_sample_size=None,
):
    unique_realizations = np.unique(df[realization_column])

    realizations = df[realization_column].values
    indices = [
        list(np.where(realizations == realization)[0])
        for realization in unique_realizations
    ]
    lengths = [len(i) for i in indices]

    if bootstrap_sample_size is None:
        bootstrap_sample_size = len(indices)

    counts = random.randint(len(indices), size=(bootstrap_size, bootstrap_sample_size))

    for selection in counts:
        selection_indices = []
        realizations = []

        for realization, k in enumerate(selection):
            selection_indices += indices[k]
            realizations += [realization] * lengths[k]

        df_sample = df.iloc[selection_indices].copy()
        df_sample[realization_column] = realizations

        yield df_sample


def apply_bootstrap(df, bootstrap_size, random, f, realization_column="realization"):
    df_bootstrap = []

    for bootstrap_realization, df_sample in enumerate(
        bootstrap(df, bootstrap_size, random, realization_column)
    ):
        df_sample = f(df_sample)
        df_sample[realization_column] = bootstrap_realization
        df_bootstrap.append(df_sample)

    return pd.concat(df_bootstrap)


def analyze_sample(
    df, realization_column="realization", columns=["weight"], statistics=None
):
    assert realization_column in df

    if columns is None or len(columns) == 0:
        assert not "count" in df.columns
        columns = ["count"]

        df = df.copy()
        df["count"] = 1.0

    for column in columns:
        assert column in df.columns

    group_columns = list(df.columns)
    for column in columns:
        group_columns.remove(column)
    group_columns.remove(realization_column)

    if statistics is None:
        statistics = {
            column: [
                ("mean", "mean"),
                ("median", "median"),
                ("min", "min"),
                ("max", "max"),
                ("q10", lambda x: x.quantile(0.1)),
                ("q90", lambda x: x.quantile(0.9)),
                ("q5", lambda x: x.quantile(0.05)),
                ("q95", lambda x: x.quantile(0.95)),
            ]
            for column in columns
        }

    df = (
        df[group_columns + columns]
        .groupby(group_columns)
        .aggregate(statistics)
        .reset_index()
    )

    return df


def analyze_sample_and_flatten(
    df, realization_column="realization", columns=["weight"], statistics=None
):
    df = analyze_sample(df, realization_column, columns, statistics)
    df.columns = [c[1] if c[0] == "weight" else c[0] for c in df.columns]
    return df


def sample_subsets(df, subset_size, random, realization_column="realization"):
    realizations = len(np.unique(df[realization_column]))
    return bootstrap(df, realizations, random, realization_column, subset_size)


def average_subsets(
    df, subset_size, random, realization_column="realization", weight_column="weight"
):
    df_output = []

    for realization, df_subset in enumerate(
        sample_subsets(df, subset_size, random, realization_column)
    ):
        df_subset = analyze_sample(
            df_subset, realization_column, weight_column, [("weight", "mean")]
        )
        df_subset[realization_column] = realization
        df_output.append(df_subset)

    return pd.concat(df_output)


if __name__ == "__main__":

    def create_sample(random_seed):
        random = np.random.RandomState(random_seed)

        index = np.arange(100)
        ages = random.randint(10, size=100) * 10
        gender = random.randint(2, size=100)

        df = pd.DataFrame.from_records(
            zip(index, ages, gender), columns=["person", "age", "gender"]
        )
        df["gender"] = df["gender"].map({0: "male", 1: "female"}).astype("category")
        df["weight"] = 1.0

        return df

    df = pd.DataFrame.from_records(
        [
            {"age": 20, "weight": 10.0, "abc": 10.0, "realization": 0},
            {"age": 50, "weight": 50.0, "abc": 50.0, "realization": 0},
            {"age": 20, "weight": 20.0, "abc": 20.0, "realization": 1},
            {"age": 50, "weight": 60.0, "abc": 60.0, "realization": 1},
        ]
    )

    random = np.random.RandomState(0)

    statistics = {
        "weight": [("mean", "mean")],
        "abc": [("q95", lambda x: x.quantile(0.95))],
    }

    df = apply_bootstrap(
        df,
        100,
        random,
        lambda df: analyze_sample(df, statistics=statistics, columns=["weight", "abc"]),
    )

    df = (
        df.groupby("age")
        .aggregate(
            [
                ("mean", "mean"),
                ("q10", lambda x: x.quantile(0.1)),
                ("q90", lambda x: x.quantile(0.9)),
            ]
        )
        .reset_index()
    )

    print(df)

    exit()

    random = np.random.RandomState(0)

    # for df_subset in sample_subsets(df, 3, random):
    #    print(df_subset)

    print(average_subsets(df, 3, random))

    print(
        apply_bootstrap(
            average_subsets(df, 3, random), 100, random, lambda df: analyze_sample(df)
        )
    )

    exit()

    # print(analyze(df))

    # for df_sample in bootstrap(df, 100, random):
    #    df_sample = analyze(df_sample)
    #    print(df_sample)

    statistics = [("precision", lambda x: np.mean(x < 55.0))]

    df = apply_bootstrap(
        df, 100, random, lambda df: analyze_sample(df, statistics=statistics)
    )
    df = (
        df.groupby(["age"])
        .aggregate(
            [
                ("mean", "mean"),
                ("q10", lambda x: x.quantile(0.1)),
                ("q90", lambda x: x.quantile(0.9)),
            ]
        )
        .reset_index()
    )

    print(df)
    exit()
    print()

    exit()

    sample = [create_sample(R) for R in range(2)]
    random = np.random.RandomState(5)

    # marginals = [marginalize(df, [("age",), ("gender",), ("age", "gender"), tuple()]) for df in sample]
    marginals = [marginalize(df, [("gender",)]) for df in sample]
    marginals = collect_marginalized_sample(marginals)

    metrics = bootstrap_sampled_marginals(marginals, 100, subset_size=2, random=random)
    print(metrics[("gender",)])
