import numpy as np
import copy
import analysis.statistics


def get_seeds(number_of_seeds):
    return np.arange(1, number_of_seeds + 1) * 1000


def configure(context, stage, sample_size, parameters={}, alias=None, ephemeral=True):
    if alias is None:
        alias = stage

    seeds = get_seeds(sample_size)

    for index, random_seed in enumerate(seeds):
        sample_parameters = copy.copy(parameters)
        sample_parameters["random_seed"] = int(random_seed)

        context.stage(
            stage,
            sample_parameters,
            alias="bootstrap_%s_%d" % (alias, index),
            ephemeral=ephemeral,
        )


def get_stage(context, alias, index):
    return context.stage("bootstrap_%s_%d" % (alias, index))


def get_stages(context, alias, sample_size):
    for index in range(sample_size):
        yield get_stage(context, alias, index)
