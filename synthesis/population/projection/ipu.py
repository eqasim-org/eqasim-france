import pandas as pd
import numpy as np

"""
This stage reweights the census data set according to the projection data for a different year.
"""


def configure(context):
    context.stage("data.census.cleaned")
    context.stage("data.census.projection")


def execute(context):
    df_census = context.stage("data.census.cleaned")
    projection = context.stage("data.census.projection")

    # Adjust projection data (see below)
    adjust_projection(projection)

    # Prepare indexing
    df_households = df_census[
        ["household_id", "household_size", "weight"]
    ].drop_duplicates("household_id")
    df_households["household_index"] = np.arange(len(df_households))
    df_census = pd.merge(df_census, df_households[["household_id", "household_index"]])

    # Obtain weights and sizes as arrays
    household_weights = df_households["weight"].values

    # Obtain the attribute levels and membership of attributes for all households
    attributes = []

    attribute_membership = []
    attribute_counts = []
    attribute_targets = []

    # Proccesing age ...
    df_marginal = projection["age"]
    for index, row in context.progress(
        df_marginal.iterrows(),
        label="Processing attribute: age",
        total=len(df_marginal),
    ):
        f = df_census["age"] == row["age"]
        assert np.count_nonzero(f) > 0

        df_counts = df_census.loc[f, "household_index"].value_counts()
        attribute_targets.append(row["projection"])
        attribute_membership.append(df_counts.index.values)
        attribute_counts.append(df_counts.values)
        attributes.append("age={}".format(row["age"]))

    # Processing sex ...
    df_marginal = projection["sex"]
    for index, row in context.progress(
        df_marginal.iterrows(),
        label="Processing attribute: sex",
        total=len(df_marginal),
    ):
        f = df_census["sex"] == row["sex"]
        f &= (df_census["age"] > 0) & (df_census["age"] <= 104)
        assert np.count_nonzero(f) > 0

        df_counts = df_census.loc[f, "household_index"].value_counts()
        attribute_targets.append(row["projection"])
        attribute_membership.append(df_counts.index.values)
        attribute_counts.append(df_counts.values)
        attributes.append("sex={}".format(row["sex"]))

    # Processing age x sex ...
    df_marginal = projection["cross"]
    for index, row in context.progress(
        df_marginal.iterrows(),
        label="Processing attributes: sex x age",
        total=len(df_marginal),
    ):
        f = (df_census["sex"] == row["sex"]) & (df_census["age"] == row["age"])
        assert np.count_nonzero(f) > 0

        df_counts = df_census.loc[f, "household_index"].value_counts()
        attribute_targets.append(row["projection"])
        attribute_membership.append(df_counts.index.values)
        attribute_counts.append(df_counts.values)
        attributes.append("sex={},age={}".format(row["sex"], row["age"]))

    # Processing total ...
    f = (df_census["age"] > 0) & (df_census["age"] <= 104)
    assert np.count_nonzero(f) > 0

    df_counts = df_census.loc[f, "household_index"].value_counts()
    attribute_targets.append(projection["total"]["projection"].values[0])
    attribute_membership.append(df_counts.index.values)
    attribute_counts.append(df_counts.values)
    attributes.append("total")

    # Perform IPU to obtain update weights
    update = np.ones((len(df_households),))

    print("Starting IPU with {} attributes".format(len(attributes)))
    convergence_threshold = 1e-3
    maximum_iterations = 100

    for iteration in range(maximum_iterations):
        factors = []
        for k in np.arange(len(attributes)):
            selection = attribute_membership[k]

            target = attribute_targets[k]
            current = np.sum(
                update[selection] * household_weights[selection] * attribute_counts[k]
            )

            factor = target / current
            factors.append(factor)

            update[selection] *= factor

        print(
            "IPU it={} min={} max={}".format(
                iteration, np.min(factors), np.max(factors)
            )
        )

        converged = np.abs(1 - np.max(factors)) < convergence_threshold
        converged &= np.abs(1 - np.min(factors)) < convergence_threshold
        if converged:
            break

    # Check that the applied factors in the last iteration are sufficiently small
    assert converged

    print(
        "IPF updates min={} max={} mean={}".format(
            np.min(update), np.max(update), np.mean(update)
        )
    )

    # Update the weights
    df_households["weight"] *= update

    return df_households[["household_id", "weight"]]


def adjust_projection(projection):
    # The projection data contains information on zero-year old persons. However, there is a big difference between the
    # RP data and the projection, probably because RP is fixed to a certain reference date and not all of them are
    # registered. We, in particular, see that there is a large jump between 0 years and 1 years.
    # Therefore, we exclude the zero-year persons from the projection. This, however, means adapting all the marginals.
    # Also, exclude everything that is 105+

    df_cross = projection["cross"]
    df_age = projection["age"]
    df_sex = projection["sex"]
    df_total = projection["total"]

    # Reduce totals from sex distribution and overall population
    for index, row in df_cross.iterrows():
        if row["age"] == 0 or row["age"] == "105+":
            f_sex = df_sex["sex"] == row["sex"]

            df_sex.loc[f_sex, "projection"] = (
                df_sex.loc[f_sex, "projection"] - row["projection"]
            )
            df_total["projection"] = df_total["projection"] - row["projection"]

    projection["sex"] = df_sex
    projection["total"] = df_total

    # Remove zero old years from cross distribution
    projection["cross"] = df_cross[(df_cross["age"] != 0) & (df_cross["age"] != "105+")]

    # Remove zero old years from age distribution
    projection["age"] = df_age[(df_age["age"] != 0) & (df_age["age"] != "105+")]
