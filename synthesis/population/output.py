"""
This stage outputs the census-based generated population (before enrichment).
"""

def configure(context):
    context.stage("synthesis.population.sampled")

    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

def execute(context):
    output_path = context.config("output_path")
    output_prefix = context.config("output_prefix")
    
    df_census = context.stage("synthesis.population.sampled")
    df_census.to_parquet("%s/%spopulation.parquet" % (output_path, output_prefix))
