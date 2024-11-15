import geopandas as gpd


def configure(context):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

    context.stage("data.bdtopo.raw")


def execute(context):
    df_buildings = context.stage("data.bdtopo.raw")

    df_buildings.to_file(
        "%s/%sbdtopo.gpkg"
        % (context.config("output_path"), context.config("output_prefix"))
    )
