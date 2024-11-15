"""
Often, we need localized SIRENE data in losely related projects. This stage
makes it easy to extract the data set from the pipeline.
"""


def configure(context):
    context.stage("data.sirene.localized")

    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")


def execute(context):
    df_sirene = context.stage("data.sirene.localized")
    df_sirene["commune_id"] = df_sirene["commune_id"].astype(str)

    df_sirene.to_file(
        "%s/%ssirene.gpkg"
        % (context.config("output_path"), context.config("output_prefix")),
        driver="GPKG",
    )
