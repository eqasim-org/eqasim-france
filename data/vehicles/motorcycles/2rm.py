import pandas as pd

"""
This stage loads the raw data of 2rm 2012 survey
https://www.statistiques.developpement-durable.gouv.fr/sites/default/files/2018-11/2rm-detail-diffusion.csv
"""

def configure(context):
    context.config("data_path")

def execute(context):
    df_motorcycles = pd.read_csv("%s/2rm/2rm-detail-diffusion.csv" % context.config("data_path"), sep=";", encoding="cp1252")

    # some filters
    df_motorcycles = df_motorcycles[df_motorcycles["KMANNUEL"] > 1] # vehicle never used
    df_motorcycles = df_motorcycles[df_motorcycles["ENDURO"].astype(int) != 1] # vehicle "tout-terrain"
    df_motorcycles = df_motorcycles[df_motorcycles["AGEVEHICULE"].astype(int) < 30] # vehicle too old

    # TODO: consider more filters
    # filter on "UTI" utilization period (1: all year w/ all weather, 2: all year w/ good weather, 3: summer)
    # filter on "FREQ" frequence suring UTI period (1: daily, 2: 4 to 5 times a week, 3: 1 to 3 times a week, 4: only weekends, 5: allmost never)
    # filter on "MVACANCES" usage during vacations (1: yes, 2: no) if MTRAVAIL, MACHAT, MLOISIRS, etc are all "no"
    
    # create PF "puissance fiscale" categories
    df_motorcycles["PFCAT"] = df_motorcycles["PF"].map({
        0: "0_50cc",
        1: "50_125cc",
        2: "125_250cc", # 125_175cc
        3: "125_250cc", # 175_250cc
        4: "250_1000cc", # 250_350cc
        5: "250_1000cc", # 350_500cc
        6: "250_1000cc", # 500_625cc
        7: "250_1000cc", # 625_750cc
        8: "250_1000cc", # 750_875cc
        9: "250_1000cc", # 875_1000cc
        10: "1000_2375cc", # 1000_1125cc
        11: "1000_2375cc", # 1125_1250cc
        12: "1000_2375cc", # 1250_1375cc
        13: "1000_2375cc", # 1375_1500cc
        14: "1000_2375cc", # 1500_1625cc
        15: "1000_2375cc", # 1625_1750cc
        16: "1000_2375cc", # 1750_1875cc
        17: "1000_2375cc", # 1875_2000cc
        18: "1000_2375cc", # 2000_2125cc
        19: "1000_2375cc", # 2125_2250cc
        20: "1000_2375cc" # 2250_2375cc
    }).astype("category")

    # map engine types
    df_motorcycles["MOTEUR"] = df_motorcycles["MOTEUR"].map({
        1: "2S",
        2: "4S",
        3: "Unknown",
        4: "Electric"
    }).astype("category")

    # if MOTEUR is unknown and PF < 50cc, then it is a 2S, else it is a 4S
    mask = (df_motorcycles["MOTEUR"] == "Unknown") & (df_motorcycles["PFCAT"] == "0_50cc")
    df_motorcycles.loc[mask, "MOTEUR"] = "2S"
    mask = (df_motorcycles["MOTEUR"] == "Unknown") & (df_motorcycles["PFCAT"] != "0_50cc")
    df_motorcycles.loc[mask, "MOTEUR"] = "4S"

    # create age categories
    bins = [14, 18, 25, 35, 50, 70, 110]
    labels = ["%d_%d" % (a,b) for a,b in zip(bins, bins[1:])]
    age_bins = { "bins": bins, "labels": labels }

    df_motorcycles["AGECAT"] = pd.cut(df_motorcycles["AGECONDUCTEUR"], bins=age_bins["bins"], labels=age_bins["labels"], right=False)

    # TODO : think about the attributes we would like to groupby on
    # possible candidates are : ["AGECAT", "SEXE", "NBVOITURES", "NBVELOS", "STATUT", "PROFESSION", "DIPLOME", "NBFOYER", "NBENFANTS", "REGION", "ZONAGE", "REVENU"]
    
    columns_persons = ["AGECAT", "SEXE"]
    columns_vehicles = ["PFCAT", "AGEVEHICULE", "MOTEUR"]
    df_motorcycles = df_motorcycles[columns_persons + columns_vehicles + ["POIDSVEHICULE", "POIDSCONDUCTEUR"]]

    df_counts = df_motorcycles.groupby(columns_persons + columns_vehicles, observed=True)["POIDSVEHICULE"].sum().reset_index()

    df_counts["SEXE"] = df_counts["SEXE"].map({ 1.0: "male", 2.0: "female" }).astype("category")

    return df_counts, age_bins