import pandas as pd
import numpy as np

"""
Clean the SIRENE enterprise census.
"""
 
def configure(context):
    context.stage("data.sirene.raw_siren", ephemeral = True)
    context.stage("data.sirene.raw_siret", ephemeral = True)
    context.stage("data.spatial.codes")
    context.config("exclude_no_employee", False)

    context.config("output_path")

def execute(context):
    df_sirene_establishments = context.stage("data.sirene.raw_siret")
    df_sirene_headquarters = context.stage("data.sirene.raw_siren")


    # Filter out establishments without a corresponding headquarter
    df_sirene = df_sirene_establishments[df_sirene_establishments["siren"].isin(df_sirene_headquarters["siren"])].copy()

    # Remove inactive enterprises 
    df_sirene = df_sirene[
        df_sirene["etatAdministratifEtablissement"] == "A"
    ].copy()

    if context.config("exclude_no_employee"):
        # exclude "NN", "00", and NaN
        df_sirene = df_sirene[
            df_sirene["trancheEffectifsEtablissement"].notna()
            & ~(df_sirene["trancheEffectifsEtablissement"].isin(["NN", "00"]))
        ].copy()

    # Define work place weights by person under salary ....
    df_sirene["minimum_employees"] = 1.0 # Includes "NN", "00", and NaN
    df_sirene["maximum_employees"] = 1.0 # Includes "NN", "00", and NaN

    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "01", "minimum_employees"] = 1.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "01", "maximum_employees"] = 2.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "02", "minimum_employees"] = 3.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "02", "maximum_employees"] = 5.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "03", "minimum_employees"] = 6.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "03", "maximum_employees"] = 9.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "11", "minimum_employees"] = 10.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "11", "maximum_employees"] = 19.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "12", "minimum_employees"] = 20.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "12", "maximum_employees"] = 49.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "21", "minimum_employees"] = 50.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "21", "maximum_employees"] = 99.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "22", "minimum_employees"] = 100.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "22", "maximum_employees"] = 199.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "31", "minimum_employees"] = 200.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "31", "maximum_employees"] = 249.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "32", "minimum_employees"] = 250.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "32", "maximum_employees"] = 499.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "41", "minimum_employees"] = 500.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "41", "maximum_employees"] = 999.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "42", "minimum_employees"] = 1000.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "42", "maximum_employees"] = 1999.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "51", "minimum_employees"] = 2000.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "51", "maximum_employees"] = 4999.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "52", "minimum_employees"] = 5000.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "52", "maximum_employees"] = 9999.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "53", "minimum_employees"] = 10000.0
    df_sirene.loc[df_sirene["trancheEffectifsEtablissement"] == "53", "maximum_employees"] = np.inf

    # Add activity classification
    df_sirene["ape"] = df_sirene["activitePrincipaleEtablissement"]

    # Check communes
    df_sirene["commune_id"] = df_sirene["codeCommuneEtablissement"].astype("category")

    df_codes = context.stage("data.spatial.codes")
    requested_communes = set(df_codes["commune_id"].unique())
    excess_communes = set(df_sirene["commune_id"].unique()) - requested_communes

    if len(excess_communes) > 0:
        print("Found excess municipalities in SIRENE data: ", excess_communes)
    
    if len(excess_communes) > 10:
        raise RuntimeError("Found more than 10 excess municipalities in SIRENE data")

    df_sirene = df_sirene[["siren", "commune_id", "minimum_employees", "maximum_employees", "ape", "siret"]]

    # Add law status
    initial_count = len(df_sirene)

    df_sirene = pd.merge(df_sirene, df_sirene_headquarters, on = "siren")

    df_sirene["law_status"] = df_sirene["categorieJuridiqueUniteLegale"]
    df_sirene = df_sirene.drop(columns =  ["categorieJuridiqueUniteLegale", "siren"])

    final_count = len(df_sirene)
    assert initial_count == final_count

    return df_sirene
