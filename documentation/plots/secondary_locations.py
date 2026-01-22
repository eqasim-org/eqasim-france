import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import documentation.plotting as plotting

def configure(context):
    context.stage("synthesis.population.spatial.secondary.distance_distributions")

    context.stage("analysis.synthesis.mode_distances")
    context.stage("analysis.reference.hts.mode_distances")

    context.config("hts")

def execute(context):
    plotting.setup()
    hts_name = context.config("hts")

    # PLOT: Input distributions
    distributions = context.stage("synthesis.population.spatial.secondary.distance_distributions")

    plt.figure()

    modes = list(context.stage("analysis.reference.hts.mode_distances").keys())

    for index, mode in enumerate(modes):
        mode_distribution = distributions[mode]
        bounds = mode_distribution["bounds"]
        bounds[~np.isfinite(bounds)] = 6 * 3600

        means = [0.0]
        q10 = [0.0]
        q90 = [0.0]

        for distribution in mode_distribution["distributions"]:
            weights = distribution["weights"] / np.sum(distribution["weights"])
            means.append(np.sum(weights * distribution["values"]))

            q10.append(distribution["values"][np.count_nonzero(distribution["cdf"] < 0.1)])
            q90.append(distribution["values"][np.count_nonzero(distribution["cdf"] < 0.9)])

        if mode in ("car", "pt"):
            plt.fill_between([0.0] + list(bounds), q10, q90, color = plotting.COLORSET5[index], alpha = 0.25, linewidth = 0.0)

        plt.plot([0.0] + list(bounds), means, label = "%s (%d)" % (plotting.MODE_LABELS[mode], len(bounds)), linewidth = 1.0, marker = ".", markersize = 3, color = plotting.COLORSET5[index])

    plt.gca().xaxis.set_major_locator(tck.FixedLocator(np.arange(100) * 60 * 20))
    plt.gca().xaxis.set_major_formatter(tck.FuncFormatter(lambda x,p: str(x // 60)))

    plt.gca().yaxis.set_major_locator(tck.FixedLocator(np.arange(100) * 5 * 1000))
    plt.gca().yaxis.set_major_formatter(tck.FuncFormatter(lambda x,p: str(x // 1000)))

    plt.legend(loc = "upper left")
    plt.xlim([0, 90 * 60 if hts_name == "egt" else 50 * 60])
    plt.ylim([0, 45 * 1000 if hts_name == "egt" else 25 * 1000])

    plt.grid()

    plt.xlabel("Travel time [min]")
    plt.ylabel("Euclidean distance [km]")

    plt.tight_layout()
    plt.savefig("%s/input_distributions.pdf" % context.path())
    plt.close()

    # PLOT: Distance distributions
    df_synthetic = context.stage("analysis.synthesis.mode_distances")
    reference_data = context.stage("analysis.reference.hts.mode_distances")

    plt.figure(figsize =  (6.0, 2.5), dpi = 100) # 2.5 * 2.5

    limits = dict(
        car = 20 * 1e3, car_passenger = 20 * 1e3, pt = 20 * 1e3,
        bicycle = 6 * 1e3, walk = 1 * 1e3
    )

    modes = ["car", "bicycle" if "bicycle" in modes else "walk" ]

    for index, mode in enumerate(modes):
        plt.subplot(1, 2, index + 1)

        mode_reference = reference_data[mode]
        plt.plot(mode_reference["values"] * 1e-3, mode_reference["cdf"], linestyle = '--', color = "k", linewidth = 1.0, label = "HTS")

        df_mode = df_synthetic[df_synthetic["mode"] == mode]
        plt.fill_betweenx(df_mode["cdf"], df_mode["min"]* 1e-3, df_mode["max"] * 1e-3, linewidth = 0.0, color = plotting.COLORS[hts_name], alpha = 0.25, label = "Range")
        plt.plot(df_mode["mean"] * 1e-3, df_mode["cdf"], color = plotting.COLORS[hts_name], linewidth = 1.0, label = "Synthetic")

        plt.xlim([0, limits[mode] * 1e-3])
        plt.ylim([0, 1])

        plt.title(plotting.MODE_LABELS[mode], fontsize = plotting.FONT_SIZE)
        plt.xlabel("Euclidean distance [km]")
        plt.grid()

        if index % 2 == 0:
            plt.ylabel("Cumulative density")

        if index % 2 == 1:
            plt.legend(loc = "best")

    plt.tight_layout()
    plt.savefig("%s/distance_distributions.pdf" % context.path())
    plt.close()
