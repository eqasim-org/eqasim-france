import numpy as np

import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting

SAMPLING_RATE = 0.05
POPULATION_SAMPLES = 200


def configure(context):
    context.stage(
        "analysis.matching",
        {
            "sampling_rate": SAMPLING_RATE,
            "analysis_populations": POPULATION_SAMPLES,
        },
        alias="data",
    )


def execute(context):
    data = context.stage("data")
    variables = max(data.keys()) + 1

    means = [np.mean(data[v] / data[0]) for v in range(variables)]
    # mins = [np.percentile(data[v] / data[0], 10) for v in range(variables)]
    # maxs = [np.percentile(data[v] / data[0], 90) for v in range(variables)]

    mins = [np.min(data[v] / data[0]) for v in range(variables)]
    maxs = [np.max(data[v] / data[0]) for v in range(variables)]

    # Prepare plot
    plotting.setup()

    plt.figure()
    plt.bar(range(variables), means, color=plotting.COLORS["synthetic"])

    for v, min, max in zip(range(variables), mins, maxs):
        plt.plot(
            [
                v,
                v,
            ],
            [min, max],
            linewidth=1,
            label="90% Conf.",
            color="k",
        )

    plt.xlabel("Variables")
    plt.ylabel("Matching rate")

    plt.gca().yaxis.set_major_locator(tck.FixedLocator(np.arange(100) * 0.2))
    plt.gca().yaxis.set_major_formatter(
        tck.FuncFormatter(lambda x, p: "%d%%" % (100 * x,))
    )

    plt.tight_layout()
    plt.savefig("%s/matching_rate.pdf" % context.path())
