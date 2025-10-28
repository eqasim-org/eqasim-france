import numpy as np
import pandas as pd
from synthesis.population.commutes.utils import clean_work_commutes

"""

"""

def configure(context):
    context.stage("data.od.cleaned")
    context.stage("data.spatial.centroid_distances")

    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.spatial.home.zones")

    context.config("random_seed")

    context.config("output_path")

def _sample_class_dist(context, args):
    csp,commune_id, random_seed = args
    df_person, df_commutes = context.data("person"), context.data("commutes_dist")

    random = np.random.RandomState(random_seed)
    df_commutes = df_commutes[(df_commutes["origin_id"]==commune_id)&(df_commutes["socioprofessional_class"] == csp)&(df_commutes["weight"]>0)]

    f = (df_person["commune_id"] == commune_id) & (df_person["socioprofessional_class"] == csp)
    df_selected = df_person[f]
    count = len(df_selected)

    if df_commutes.empty : 
        return f,np.empty(count).fill(np.nan)
    
    weight = df_commutes["weight"].values / df_commutes["weight"].sum()


    dist_counts = random.multinomial(count, weight)

    class_dist = df_commutes["distance_class"].values
    class_dist = np.repeat(class_dist, dist_counts)
    random.shuffle(class_dist)

    return f, class_dist

def execute(context):
    random = np.random.RandomState(context.config("random_seed"))

    # Load data 
    df_work,_ = context.stage("data.od.cleaned")
    df_spatial = context.stage("data.spatial.centroid_distances")
    df_work = clean_work_commutes(df_work,df_spatial)

    df_person = context.stage("synthesis.population.sampled")[[
        "person_id","household_id", "socioprofessional_class",
    ]]
    df_homes = context.stage("synthesis.population.spatial.home.zones")[[
        "household_id", "commune_id"
    ]]

    df_person = pd.merge(df_person, df_homes)

    # Perform sampling per commune and csp
    with context.parallel(dict(person = df_person, commutes_dist = df_work)) as parallel:
        csp_commune_ids = df_person[df_person["socioprofessional_class"]<=6][["socioprofessional_class","commune_id"]].drop_duplicates()
        random_seeds = random.randint(10000, size = len(csp_commune_ids))

        for f, class_dist in context.progress(parallel.imap(_sample_class_dist, zip(csp_commune_ids["socioprofessional_class"].values,csp_commune_ids["commune_id"].values, random_seeds)), label = "Imputing distance class ...", total = len(csp_commune_ids)):

            df_person.loc[f, "distance_class"] = class_dist

    # Cleanup
    df_person = df_person[["person_id","household_id", "socioprofessional_class", "distance_class"]]
    assert len(df_person) == len(df_person["person_id"].unique())
    return df_person