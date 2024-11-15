import numpy as np
import pandas as pd

import analysis.marginals as marginals
import analysis.statistics as stats

MARGINALS = [
    ("age_class",),
    ("sex",),
    ("employed",),
    ("studies",),
    ("socioprofessional_class",),
    ("age_class", "employed"),
]


def configure(context):
    context.config("random_seed")
    context.stage(
        "synthesis.population.sampled",
        dict(random_seed=context.config("random_seed")),
        alias="sample",
    )


def execute(context):
    df = context.stage("sample")
    marginals.prepare_classes(df)
    return stats.marginalize(df, MARGINALS, weight_column=None)
