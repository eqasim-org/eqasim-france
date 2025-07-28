import os
import polars as pl
import zipfile

"""
This stages loads a file containing all spatial codes in France and how
they can be translated into each other. These are mainly IRIS, commune,
departement and région.
"""

def configure(context):
    context.config("data_path")

    context.config("regions", [11])
    context.config("departments", [])
    context.config("codes_path", "codes_2021/reference_IRIS_geo2021.zip")
    context.config("codes_xlsx", "reference_IRIS_geo2021.xlsx")

def execute(context):
    # Load IRIS registry
    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("codes_path"))) as archive:
        with archive.open(context.config("codes_xlsx")) as f:
            df_codes = pl.read_excel(
                f.read(),
                sheet_name="Emboitements_IRIS",
                columns=["CODE_IRIS", "DEPCOM", "DEP", "REG"],
                read_options={"header_row": 5},
                schema_overrides={
                    "CODE_IRIS": pl.String,
                    "DEPCOM": pl.String,
                    "DEP": pl.String,
                    "REG": pl.Int32,
                },
            ).rename({
                "CODE_IRIS": "iris_id",
                "DEPCOM": "commune_id",
                "DEP": "departement_id",
                "REG": "region_id",
            })

    # Filter zones
    requested_regions = list(map(int, context.config("regions")))
    requested_departments = list(map(str, context.config("departments")))

    if len(requested_regions) > 0:
        df_codes = df_codes.filter(pl.col("region_id").is_in(requested_regions))

    if len(requested_departments) > 0:
        df_codes = df_codes.filter(pl.col("departement_id").is_in(requested_departments))

    df_codes = df_codes.with_columns(
        pl.col("iris_id").cast(pl.Categorical),
        pl.col("commune_id").cast(pl.Categorical),
        pl.col("departement_id").cast(pl.Categorical),
    )

    return df_codes.to_pandas()

def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("codes_path"))):
        raise RuntimeError("Spatial reference codes are not available")

    return os.path.getsize("%s/%s" % (context.config("data_path"), context.config("codes_path")))
