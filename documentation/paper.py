import shutil


def configure(context):
    context.stage("documentation.plots.data.hts_comparison")
    # context.stage("documentation.plots.theory.sampling_error")
    context.stage("documentation.plots.monte_carlo")
    context.stage("documentation.plots.income")

    context.stage("documentation.plots.sociodemographics.general")
    context.stage("documentation.plots.sociodemographics.local")
    context.stage("documentation.plots.sociodemographics.chains")

    context.stage("documentation.plots.commute_flow")
    context.stage("documentation.plots.commute_distance")

    context.stage("documentation.plots.secondary_locations")

    context.stage("documentation.shapes")
    context.stage("documentation.info.tex")

    context.config("paper_path")


def execute(context):
    paper_path = context.config("paper_path")

    # Copy plots and tables
    mapping = {
        "hts_comparison_distance.pdf": (
            "documentation.plots.data.hts_comparison",
            "distance_distribution.pdf",
        ),
        "hts_comparison_age.pdf": (
            "documentation.plots.data.hts_comparison",
            "age_distribution.pdf",
        ),
        # "theory_sampling_error.pdf": ("documentation.plots.theory.sampling_error", "sampling_error.pdf"),
        # "sampling_sample_count.pdf": ("documentation.plots.sampling.sample_count", "sample_count.pdf"),
        # "sampling_error_probability.pdf": ("documentation.plots.sampling.error_probability", "error_probability.pdf"),
        "monte_carlo.pdf": ("documentation.plots.monte_carlo", "monte_carlo.pdf"),
        "monte_carlo_table.tex": (
            "documentation.plots.monte_carlo",
            "monte_carlo_table.tex",
        ),
        "income_distributions.pdf": (
            "documentation.plots.income",
            "income_distributions.pdf",
        ),
        "socdem_comparison_persons.pdf": (
            "documentation.plots.sociodemographics.general",
            "person.pdf",
        ),
        "socdem_comparison_households.pdf": (
            "documentation.plots.sociodemographics.general",
            "household.pdf",
        ),
        "socdem_spatial_comparison.pdf": (
            "documentation.plots.sociodemographics.local",
            "comparison.pdf",
        ),
        "activity_chain_comparison.pdf": (
            "documentation.plots.sociodemographics.chains",
            "activity_chains.pdf",
        ),
        "commute_flow_bars.pdf": (
            "documentation.plots.commute_flow",
            "commute_flows.pdf",
        ),
        "commute_flow_boxplot.pdf": (
            "documentation.plots.commute_flow",
            "commute_flow_boxplot.pdf",
        ),
        "commute_distance_cdf.pdf": (
            "documentation.plots.commute_distance",
            "commute_distance_cdf.pdf",
        ),
        "secloc_distributions.pdf": (
            "documentation.plots.secondary_locations",
            "input_distributions.pdf",
        ),
        "secloc_output.pdf": (
            "documentation.plots.secondary_locations",
            "distance_distributions.pdf",
        ),
        "income.geojson": ("documentation.shapes", "income.geojson"),
        "info.tex": ("documentation.info.tex", "info.tex"),
    }

    for target, (stage, path) in mapping.items():
        shutil.copy(
            "%s/%s" % (context.path(stage), path), "%s/%s" % (paper_path, target)
        )
