import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as stats
import documentation.plotting as plotting


def get_count_distribution(ns, w, s):
    l, u = np.floor(w), np.ceil(w)
    p = w - l

    Fl = stats.binom(l, s).cdf(ns)
    Fu = stats.binom(u, s).cdf(ns)

    return p * Fu + (1 - p) * Fl


def get_error_probability(ws, s, q):
    probabilities = []

    for w in ws:
        l = np.floor(s * w * (1 - q))
        u = np.floor(s * w * (1 + q))

        Fl, Fu = get_count_distribution([l, u], w, s)
        probabilities.append(Fu - Fl)

    return probabilities


def configure(context):
    pass


def execute(context):
    plotting.setup()

    q = 0.01

    plt.figure(figsize=plotting.WIDE_FIGSIZE)

    for s, color in zip([0.01, 0.1, 0.25], ["#000000", "#777777", "#cccccc"]):
        ws = np.linspace(0, 2000, 10000)

        probs = get_error_probability(ws, s, q)
        plt.plot(ws, probs, ".", label="s = %.2f" % s, color=color, markersize=2)

    plt.legend(loc="best")
    plt.grid()
    plt.xlabel("Reference weight")
    plt.ylabel("Probability")
    plt.tight_layout()

    plt.savefig("%s/sampling_error.pdf" % context.path())
