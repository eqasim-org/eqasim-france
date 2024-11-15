import geopandas as gpd


def configure(context):
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

    context.stage("data.bdtopo.raw")
    context.stage("synthesis.locations.home.locations")


def execute(context):
    # Load data
    df_buildings = context.stage("data.bdtopo.raw")[
        ["building_id", "housing", "geometry"]
    ]

    df_locations = context.stage("synthesis.locations.home.locations")[
        ["location_id", "weight", "building_id", "geometry"]
    ]

    # Write into same file with multiple layers
    df_buildings.to_file(
        "%s/%shousing.gpkg"
        % (context.config("output_path"), context.config("output_prefix")),
        layer="buildings",
    )

    df_locations.to_file(
        "%s/%shousing.gpkg"
        % (context.config("output_path"), context.config("output_prefix")),
        layer="addresses",
    )
