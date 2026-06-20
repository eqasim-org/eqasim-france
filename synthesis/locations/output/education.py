def configure(context):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

    context.stage("synthesis.locations.education")

def execute(context):
    # load data
    df_locations = context.stage("synthesis.locations.education")

    df_locations.to_file("%s/%seducation_locations.gpkg" % (
        context.config("output_path"), context.config("output_prefix")
    ))
