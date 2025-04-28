from tqdm import tqdm
import pandas as pd
import os
import zipfile

"""
This stage loads the raw data of the French HTS (EMP).
"""

Q_MENAGE_COLUMNS = [ "IDENT_MEN", "pond_menC",
    "JNBVELOAD",
    "JNBVEH", "JNBMOTO", "JNBCYCLO"
]

Q_TCM_MENAGE_COLUMNS = [
    "ident_men","NPERS","pond_menC",  "decile_rev",
    "DEP_RES","REG_res",   "STATUTCOM_UU_RES"
]

K_INDIVIDU_COLUMNS = [
    "IDENT_IND", "IDENT_MEN",
    "pond_indC", "BPERMIS", "BCARTABON","ETUDIE"
]

Q_TCM_INDIVIDU_COLUMNS = [
    "ident_ind", "ident_men", "SEXE",
]
Q_TCM_INDIVIDU_KISH_COLUMNS = [
    "AGE", "ident_ind", "ident_men",
    "CS24", "SEXE", "SITUA",
]

K_DEPLOC_COLUMNS = [
    "IDENT_IND", "MMOTIFDES", "MOTPREC",
    "TYPEJOUR", "MORIHDEP", "MDESHARR", "MDISTTOT_fin",
    "MDATE_jour","MDATE_mois", "mtp",
    "REG_ORI", "REG_DES", "nb_dep",
    "POND_JOUR"
]

def configure(context):
    context.config("data_path")

    context.config("regions", [11])
    context.config("departments", [])
    #context.config("codes_path", "emp_2019/emp_2019_donnees_individuelles_anonymisees.zip")

def execute(context):
     # Load IRIS registry
    with zipfile.ZipFile(
        f'{context.config("data_path")}/emp_2019/emp_2019_donnees_individuelles_anonymisees_novembre2024.zip') as archive: 
        with archive.open("k_individu_public_V3.csv") as f:    
            df_individu = pd.read_csv(f,
                sep = ";", encoding = "latin1", usecols = K_INDIVIDU_COLUMNS,
            )    
        with archive.open("tcm_ind_public_V3.csv") as f:
            df_tcm_individu = pd.read_csv(f,
                sep = ";", encoding = "latin1", usecols = Q_TCM_INDIVIDU_COLUMNS,
            )
        with archive.open("tcm_ind_kish_public_V3.csv") as f:
            df_tcm_individu_kish = pd.read_csv(f,
                sep = ";", encoding = "latin1", usecols = Q_TCM_INDIVIDU_KISH_COLUMNS,
            )
        with archive.open("q_menage_public_V3.csv") as f:
            df_menage = pd.read_csv(f,
                sep = ";", encoding = "latin1", usecols = Q_MENAGE_COLUMNS,
                )
         
        with archive.open("tcm_men_public_V3.csv") as f:
            df_tcm_menage = pd.read_csv(f,
                sep = ",", encoding = "latin1", usecols = Q_TCM_MENAGE_COLUMNS,
                dtype = { "DEP_RES": str })
        
        with archive.open("5. k_deploc_public_V4.csv") as f:
            df_deploc = pd.read_csv(f,
                sep = ",", encoding = "latin1", usecols = K_DEPLOC_COLUMNS,
                )
        
    return df_individu, df_tcm_individu,df_tcm_individu_kish, df_menage, df_tcm_menage, df_deploc

def validate(context):
    if not os.path.exists(f'{context.config("data_path")}/emp_2019/emp_2019_donnees_individuelles_anonymisees_novembre2024.zip'):
        raise RuntimeError("Files for EMP are not available")

    return os.path.getsize(f'{context.config("data_path")}/emp_2019/emp_2019_donnees_individuelles_anonymisees_novembre2024.zip')
