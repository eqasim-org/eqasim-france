def configure(context):
    context.config("activity_purposes", ["leisure", "shop", "escort", "task"])
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
    # Set purpose to `other` for HTS purposes which are not primary purposes or declared secondary
    # purposes.
    all_purposes = {"home", "work", "education"} | set(context.config("activity_purposes"))
    df_trips.loc[~df_trips["preceding_purpose"].isin(all_purposes), "preceding_purpose"] = "other"
    df_trips.loc[~df_trips["following_purpose"].isin(all_purposes), "following_purpose"] = "other"
    df_trips["following_purpose"] = df_trips["following_purpose"].astype("category")
    df_trips["preceding_purpose"] = df_trips["preceding_purpose"].astype("category")
    return df_households, df_persons, df_trips
