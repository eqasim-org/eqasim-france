def configure(context):
    context.config("escort_purpose", False)
    hts = context.config("hts")

    if hts == "mobisurvstd":
        context.stage("data.hts.mobisurvstd.filtered", alias = "hts")
    elif hts == "egt":
        context.stage("data.hts.egt.filtered", alias = "hts")
    elif hts == "entd":
        context.stage("data.hts.entd.reweighted", alias = "hts")
    elif hts == "edgt_lyon":
        context.stage("data.hts.edgt_lyon.reweighted", alias = "hts")
    elif hts == "edgt_44":
        context.stage("data.hts.edgt_44.reweighted", alias = "hts")
    elif hts == "emp":
        context.stage("data.hts.emp.reweighted", alias = "hts")
    else:
        raise RuntimeError("Unknown HTS: %s" % hts)

def execute(context):
    df_households, df_persons, df_trips = context.stage("hts")
    if not context.config("escort_purpose"):
        df_trips.loc[df_trips["preceding_purpose"] == "escort", "preceding_purpose"] = "other"
        df_trips.loc[df_trips["following_purpose"] == "escort", "following_purpose"] = "other"
    return df_households, df_persons, df_trips
