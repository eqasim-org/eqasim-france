import pandas as pd
import numpy as np
import os
import zipfile

"""
Loads the regional aggregated income distribution.
"""

def configure(context):
    context.config("data_path")
    context.config("income_reg_path", "filosofi_2021/indic-struct-distrib-revenu-2021-SUPRA_XLSX.zip")
    context.config("income_reg_xlsx", "FILO2021_DISP_REG.xlsx")
    context.config("income_year", 21)

def execute(context):
    with zipfile.ZipFile("{}/{}".format(
        context.config("data_path"), context.config("income_reg_path"))) as archive:
        with archive.open(context.config("income_reg_xlsx")) as f:
            df = pd.read_excel(f,
                sheet_name = "ENSEMBLE", skiprows = 5,engine="calamine"
            )
            # correct data type
            df.replace("s",np.nan,inplace=True)
            df.replace("nd",np.nan,inplace=True)
    values = df[df["CODGEO"] == 11][
        [
            i + str(context.config("income_year"))
            for i in ["D1", "D2", "D3", "D4", "Q2", "D6", "D7", "D8", "D9"]
        ]
    ].values[0]

    return values

def validate(context):
    if not os.path.exists("%s/%s" % (context.config("data_path"), context.config("income_reg_path"))):
        raise RuntimeError("Regional Filosofi data is not available")

    return os.path.getsize("%s/%s" % (context.config("data_path"), context.config("income_reg_path")))
