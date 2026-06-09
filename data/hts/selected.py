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
    
    context.config("weekday", "any")

def execute(context):
    df_households, df_persons, df_trips = context.stage("hts")

    # weekday filtering
    weekday = context.config("weekday")
    if weekday != "any":
        if "weekday" not in df_persons:
            raise RuntimeError("The weekday attribute has not been implemented yet for your selected survey. Cannot perform chain matching by weekday.")
        
        # select persons by weekday
        if isinstance(weekday, str):
            df_persons = df_persons[df_persons["weekday"] == weekday].copy()
        else:
            df_persons = df_persons[df_persons["weekday"].isin(weekday)].copy()

        # adjust households and trips accordingly
        df_households = df_households[df_households["household_id"].isin(df_persons["household_id"])]
        df_trips = df_trips[df_trips["person_id"].isin(df_persons["person_id"])]

    # Set purpose to `other` for HTS purposes which are not primary purposes or declared secondary
    # purposes.
    all_purposes = {"home", "work", "education"} | set(context.config("activity_purposes"))
    df_trips.loc[~df_trips["preceding_purpose"].isin(all_purposes), "preceding_purpose"] = "other"
    df_trips.loc[~df_trips["following_purpose"].isin(all_purposes), "following_purpose"] = "other"
    df_trips["following_purpose"] = df_trips["following_purpose"].astype("category")
    df_trips["preceding_purpose"] = df_trips["preceding_purpose"].astype("category")
    
    return df_households, df_persons, df_trips
