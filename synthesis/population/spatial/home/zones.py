import numpy as np
import pandas as pd

"""
This stage samples home zones for all synthesized households. From the census
data we have several special cases that we need to cover:
- For people that live in municipalities without IRIS, only their departement is known
- For people that live in IRIS with less than 200 inhabitants, only their municipality is known

Based on these criteria, we can attach a random commune from the departement (which is not
covered by IRIS) to the first case, and we can attach a random IRIS within a commune that
has less than 200 inhabitants to the second case.
"""

def configure(context):
    context.stage("synthesis.population.sampled")

    context.stage("data.spatial.municipalities")
    context.stage("data.spatial.iris")
    context.stage("data.spatial.population")

    context.config("random_seed")

def execute(context):
    random = np.random.default_rng(context.config("random_seed"))

    df_households = context.stage("synthesis.population.sampled").drop_duplicates("household_id")[[
        "household_id", "commune_id", "iris_id", "departement_id"
    ]].copy().set_index("household_id")

    f_has_commune = df_households["commune_id"] != "undefined"
    f_has_iris = df_households["iris_id"] != "undefined"

    # Fix missing communes (we select from those without IRIS)
    df_municipalities = context.stage("data.spatial.municipalities").set_index("commune_id")
    df_municipalities["population"] = context.stage("data.spatial.population").groupby("commune_id")["population"].sum()

    df_households["commune_id"] = df_households["commune_id"].cat.add_categories(
        sorted(set(df_municipalities.index.unique()) - set(df_households["commune_id"].cat.categories)))

    departements = df_households[~f_has_commune]["departement_id"].unique()

    for departement_id in context.progress(departements, label = "Fixing missing communes ..."):
        df_candidates = df_municipalities[
            ~df_municipalities["has_iris"] &
            (df_municipalities["departement_id"].astype(str) == departement_id)]

        df_target = df_households[
            ~f_has_commune &
            (df_households["departement_id"] == departement_id)].copy()

        weights = df_candidates["population"].values.astype(float)
        weights /= np.sum(weights)

        indices = np.repeat(np.arange(weights.shape[0]), random.multinomial(len(df_target), weights))
        df_target["commune_id"] = df_candidates.reset_index()["commune_id"].iloc[indices].values

        df_households.loc[df_target.index, "commune_id"] = df_target["commune_id"]

    # Fix missing IRIS (we select from those with <200 inhabitants)
    df_iris = context.stage("data.spatial.iris").set_index("iris_id")
    df_iris["population"] = context.stage("data.spatial.population").set_index("iris_id")["population"]

    df_households["iris_id"] = df_households["iris_id"].cat.add_categories(
        sorted(set(df_iris.index.unique()) - set(df_households["iris_id"].cat.categories)))

    communes = df_households[~f_has_iris & f_has_commune]["commune_id"].unique()

    for commune_id in context.progress(communes, label = "Fixing missing IRIS ..."):
        df_candidates = df_iris[
            (df_iris["population"] <= 200) &
            (df_iris["commune_id"].astype(str) == commune_id)]

        df_target = df_households[
            f_has_commune & ~f_has_iris &
            (df_households["commune_id"] == commune_id)].copy()

        weights = df_candidates["population"].values.astype(float)
        if (weights == 0.0).all(): weights += 1.0
        weights /= np.sum(weights)

        indices = np.repeat(np.arange(weights.shape[0]), random.multinomial(len(df_target), weights))
        df_target["iris_id"] = df_candidates.reset_index()["iris_id"].iloc[indices].values

        df_households.loc[df_target.index, "iris_id"] = df_target["iris_id"]

    # Check that everybody has a commune now
    assert np.count_nonzero(df_households["commune_id"] == "undefined") == 0

    # Now there are some people left who don't have an IRIS, because the commune
    # is not covered in IRIS. Hence, we drive the commune-based IRIS for them.
    f = df_households["iris_id"] == "undefined"
    df_households.loc[f, "iris_id"] = df_households.loc[f, "commune_id"].astype(str) + "0000"

    # Finally, make sure that we have no invalid codes
    invalid_communes = set(df_households["commune_id"].unique()) - set(df_municipalities.index.unique())
    invalid_iris = set(df_households["iris_id"].unique()) - set(df_iris.index.unique())

    assert len(invalid_communes) == 0
    assert len(invalid_iris) == 0
    assert np.count_nonzero(df_households["iris_id"] == "undefined") == 0

    return df_households.reset_index()[["household_id", "departement_id", "commune_id", "iris_id"]]
