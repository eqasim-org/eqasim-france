import numpy as np

# used to evaluate maximum income value by multiplying it with the last decile value
MAXIMUM_INCOME_FACTOR = 1.2


def income_uniform_sample(random_state, deciles, size):
    """
    Draw income values from the given deciles.

    A random decile interval is chosen, then a value is uniformly drawn between the
    interval lower and upper bounds.

    For the first interval, lower bound is 0.
    For the last interval, upper bound is MAXIMUM_INCOME_FACTOR*lower_bound.

    :param random_state: numpy.random.RandomState
    :param deciles: deciles values
    :param size: income sample size
    """
    deciles = np.array([0] + deciles + [np.max(deciles) * MAXIMUM_INCOME_FACTOR])

    indices = random_state.randint(10, size=size)
    lower_bounds, upper_bounds = deciles[indices], deciles[indices + 1]

    incomes = lower_bounds + random_state.random_sample(size=size) * (upper_bounds - lower_bounds)

    return incomes
