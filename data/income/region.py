import pandas as pd
import os
import zipfile

"""
Loads the regional aggregated income distribution.
"""


def configure(context):
    context.config("data_path")
    context.config(
        "income_reg_path", "filosofi_2019/indic-struct-distrib-revenu-2019-SUPRA.zip"
    )
    context.config("income_reg_xlsx", "FILO2019_DISP_REG.xlsx")
    context.config("income_year", 19)


def execute(context):
    with zipfile.ZipFile(
        "{}/{}".format(context.config("data_path"), context.config("income_reg_path"))
    ) as archive:
        with archive.open(context.config("income_reg_xlsx")) as f:
            df = pd.read_excel(f, sheet_name="ENSEMBLE", skiprows=5)

    values = df[df["CODGEO"] == 11][
        [
            i + str(context.config("income_year"))
            for i in ["D1", "D2", "D3", "D4", "Q2", "D6", "D7", "D8", "D9"]
        ]
    ].values[0]

    return values


def validate(context):
    if not os.path.exists(
        "%s/%s" % (context.config("data_path"), context.config("income_reg_path"))
    ):
        raise RuntimeError("Regional Filosofi data is not available")

    return os.path.getsize(
        "%s/%s" % (context.config("data_path"), context.config("income_reg_path"))
    )
