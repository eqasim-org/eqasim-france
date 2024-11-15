import pandas as pd
import os
import zipfile
import numpy as np

# START Money patching openpyxl to parse INSEE file
from openpyxl.styles.colors import WHITE, RGB

__old_rgb_set__ = RGB.__set__


def __rgb_set_fixed__(self, instance, value):
    try:
        __old_rgb_set__(self, instance, value)
    except ValueError as e:
        if e.args[0] == "Colors must be aRGB hex values":
            __old_rgb_set__(self, instance, WHITE)


RGB.__set__ = __rgb_set_fixed__
# END Monkey patching openpyxl

# Loads the input data for the urban type (unité urbain)


def configure(context):
    context.stage("data.spatial.municipalities")

    context.config("data_path")
    context.config("urban_type_path", "urban_type/UU2020_au_01-01-2023.zip")


def execute(context):
    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("urban_type_path"))
    ) as archive:
        assert len(archive.filelist) == 1
        with archive.open(archive.filelist[0]) as f:
            df = pd.read_excel(f, sheet_name="Composition_communale", skiprows=5)

    df = df[["CODGEO", "STATUT_2017"]].copy()
    df = df.set_axis(["commune_id", "urban_type"], axis="columns")

    # Cities that have districts are not detailed in the UU file, only the whole city is mentioned
    # However the municipalities file details the districts with their respective INSEE codes
    cities_with_districts = {
        "75056": [str(75101 + i) for i in (range(20))],  # Paris
        "69123": [str(69001 + i) for i in range(9)],  # Lyon
        "13055": [str(13201 + i) for i in range(15)],
    }  # Marseilles

    # Replacing each line of the UU file corresponding to a city with districts by multiple lines one for each districts
    for city_code in cities_with_districts:
        base_type = df[df["commune_id"] == city_code].iloc[0]["urban_type"]
        replacement_codes = cities_with_districts[city_code]

        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    {
                        "commune_id": replacement_codes,
                        "urban_type": [base_type] * len(replacement_codes),
                    }
                ),
            ]
        )

    df = df[~df["commune_id"].isin(cities_with_districts.keys())]

    # Clean unités urbaines
    df["urban_type"] = df["urban_type"].replace(
        {"B": "suburb", "C": "central_city", "I": "isolated_city", "H": "none"}
    )
    assert np.all(~df["urban_type"].isna())
    df["urban_type"] = df["urban_type"].astype("category")

    df_municipalities = context.stage("data.spatial.municipalities")
    requested_communes = set(df_municipalities["commune_id"].unique())
    df = df[df["commune_id"].isin(requested_communes)]

    assert len(df["commune_id"].unique()) == len(df)

    return df


def validate(context):
    if not os.path.exists(
        "%s/%s" % (context.config("data_path"), context.config("urban_type_path"))
    ):
        raise RuntimeError("Urban type data is not available")

    return os.path.getsize(
        "%s/%s" % (context.config("data_path"), context.config("urban_type_path"))
    )
