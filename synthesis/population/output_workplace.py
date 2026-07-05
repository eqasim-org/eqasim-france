def configure(context):
    context.stage("synthesis.population.spatial.primary.locations")

    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

def execute(context):
    output_path = context.config("output_path")
    output_prefix = context.config("output_prefix")
    
    df_locations = context.stage("synthesis.population.spatial.primary.locations")[0]
    df_locations.to_parquet("%s/%sworkplaces.parquet" % (output_path, output_prefix))
