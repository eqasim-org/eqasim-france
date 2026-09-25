def configure(context):
    context.config("activity_purposes", ["leisure", "shop"])
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
    elif hts == "emc2":
        context.stage("data.hts.emc2_33.reweighted", alias = "hts")
    else:
        raise RuntimeError("Unknown HTS: %s" % hts)
    
    context.config("weekday", "workday")

def execute(context):
    df_households, df_persons, df_trips = context.stage("hts")

    # weekday filtering
    weekday_filter = context.config("weekday")
    has_weekday = "weekday" in df_persons

    if not has_weekday and weekday_filter != "workday":
        raise RuntimeError("The weekday attribute has not been implemented yet for your selected survey. Cannot perform chain matching by weekday. Set weekday to the default 'workday'.")

    else:
        if weekday_filter == "any":
            weekday_filter = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
        elif weekday_filter == "workday":
            weekday_filter = ("monday", "tuesday", "wednesday", "thursday", "friday")
        elif weekday_filter == "weekend":
            weekday_filter = ("saturday", "sunday")
        elif isinstance(weekday_filter, str):
            weekday_filter = [weekday_filter]

        for item in weekday_filter:
            if item not in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
                raise RuntimeError(f"Invalid element {item} in weekday filter")
        
        # select persons by weekday
        df_persons = df_persons[df_persons["weekday"].isin(weekday_filter)].copy()

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
