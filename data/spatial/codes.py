import os
import pandas as pd
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
    context.config("codes_path", "codes_2023/reference_IRIS_geo2023.zip")
    context.config("codes_xlsx", "reference_IRIS_geo2023.xlsx")

def execute(context):
    # Load IRIS registry
    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("codes_path"))) as archive:
        with archive.open(context.config("codes_xlsx")) as f:
            df_codes = pd.read_excel(f,
                skiprows = 5, sheet_name = "Emboitements_IRIS"
            )[["CODE_IRIS", "DEPCOM", "DEP", "REG"]].rename(columns = {
                "CODE_IRIS": "iris_id",
                "DEPCOM": "commune_id",
                "DEP": "departement_id",
                "REG": "region_id"
            })

    df_codes["iris_id"] = df_codes["iris_id"].astype("category")
    df_codes["commune_id"] = df_codes["commune_id"].astype("category")
    df_codes["departement_id"] = df_codes["departement_id"].astype("category")
    df_codes["region_id"] = df_codes["region_id"].astype(int)

    # Filter zones
    requested_regions = list(map(int, context.config("regions")))
    requested_departments = list(map(str, context.config("departments")))

    if len(requested_regions) > 0:
        df_codes = df_codes[df_codes["region_id"].isin(requested_regions)]

    if len(requested_departments) > 0:
        df_codes = df_codes[df_codes["departement_id"].isin(requested_departments)]

    df_codes["iris_id"] = df_codes["iris_id"].cat.remove_unused_categories()
    df_codes["commune_id"] = df_codes["commune_id"].cat.remove_unused_categories()
    df_codes["departement_id"] = df_codes["departement_id"].cat.remove_unused_categories()

    return df_codes

def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("codes_path"))):
        raise RuntimeError("Spatial reference codes are not available")

    return os.path.getsize("%s/%s" % (context.config("data_path"), context.config("codes_path")))
