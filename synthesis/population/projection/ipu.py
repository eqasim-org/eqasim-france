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
    df_projection = context.stage("data.census.projection")

    # Prepare indexing
    df_households = df_census[["household_id", "household_size", "weight"]].drop_duplicates("household_id")
    df_households["household_index"] = np.arange(len(df_households))
    df_census = pd.merge(df_census, df_households[["household_id", "household_index"]])

    # Obtain weights and sizes as arrays
    household_weights = df_households["weight"].values

    # Obtain the attribute levels and membership of attributes for all households
    attribute_membership = []
    attribute_counts = []
    attribute_targets = []

    for index, row in context.progress(df_projection.iterrows(), total = len(df_projection), label = "Processing marginals"):
        f = df_census["sex"] == row["sex"]
        f &= df_census["age"].between(row["minimum_age"], row["maximum_age"] - 1)
        f &= df_census["departement_id"] == row["department_id"]
        assert np.count_nonzero(f) > 0

        df_counts = df_census.loc[f, "household_index"].value_counts()
        attribute_targets.append(row["weight"])
        attribute_membership.append(df_counts.index.values)
        attribute_counts.append(df_counts.values)

    # Perform IPU to obtain update weights
    update = np.ones((len(df_households),))

    print("Starting IPU with {} attributes".format(len(attribute_membership)))
    convergence_threshold = 1e-3
    maximum_iterations = 100

    for iteration in range(maximum_iterations):
        factors = []    
        for k in np.arange(len(attribute_membership)):
            selection = attribute_membership[k]
        
            target = attribute_targets[k]
            current = np.sum(update[selection] * household_weights[selection] * attribute_counts[k])
        
            factor = target / current
            factors.append(factor)
                
            update[selection] *= factor

        print("IPU it={} min={} max={}".format(iteration, np.min(factors), np.max(factors)))

        converged = np.abs(1 - np.max(factors)) < convergence_threshold
        converged &= np.abs(1 - np.min(factors)) < convergence_threshold
        if converged: break

    # Check that the applied factors in the last iteration are sufficiently small
    assert converged

    print("IPF updates min={} max={} mean={}".format(np.min(update), np.max(update), np.mean(update)))

    # Update the weights
    df_households["weight"] *= update
    
    return df_households[["household_id", "weight"]]
