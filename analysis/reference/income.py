import numpy as np
import pandas as pd

import data.hts.egt.cleaned
import data.hts.entd.cleaned


def configure(context):
    context.stage("data.hts.entd.cleaned")
    context.stage("data.hts.egt.cleaned")
    context.stage("data.income.region")


def calculate_cdf(df):
    weights = df["household_weight"].values
    incomes = df["income"].values

    sorter = np.argsort(incomes)
    cdf = np.cumsum(weights[sorter]) / np.sum(weights)

    return dict(income=incomes[sorter], cdf=cdf)


def execute(context):
    # Calculate ENTD income distribution
    df_entd = context.stage("data.hts.entd.cleaned")[0][
        ["household_weight", "income_class", "consumption_units"]
    ].copy()
    entd_upper_bounds = data.hts.entd.cleaned.INCOME_CLASS_BOUNDS
    entd_lower_bounds = [0] + entd_upper_bounds[:-1]

    df_entd["income"] = (
        12
        * 0.5
        * df_entd["income_class"].apply(
            lambda k: entd_lower_bounds[k] + entd_upper_bounds[k] if k >= 0 else np.nan
        )
    )
    df_entd = pd.DataFrame(calculate_cdf(df_entd))
    df_entd["source"] = "entd"

    # Calculate EGT income distribution
    df_egt = context.stage("data.hts.egt.cleaned")[0][
        ["household_weight", "income_class", "consumption_units"]
    ].copy()
    egt_upper_bounds = data.hts.egt.cleaned.INCOME_CLASS_BOUNDS
    egt_lower_bounds = [0] + egt_upper_bounds[:-1]

    df_egt["income"] = (
        12
        * 0.5
        * df_egt["income_class"].apply(
            lambda k: egt_lower_bounds[k] + egt_upper_bounds[k] if k >= 0 else np.nan
        )
    )
    df_egt["income"] /= df_egt["consumption_units"]
    df_egt = pd.DataFrame(calculate_cdf(df_egt))
    df_egt["source"] = "egt"

    # Calcultae FiLo income distribution
    df_filo = context.stage("data.income.region")
    df_filo = pd.DataFrame(
        dict(
            income=np.array([0.0] + df_filo.tolist()),
            cdf=np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]),
        )
    )
    df_filo["source"] = "filo"

    return pd.concat([df_entd, df_egt, df_filo])
