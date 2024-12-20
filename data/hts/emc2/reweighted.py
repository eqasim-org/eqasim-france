def configure(context):
    context.stage("data.hts.emc2.filtered")

def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.emc2.filtered")

    # EMC2 defines multiple weights. For comparison with EGT we keep them in the
    # data set for the previous stages. In this one we override the weight,
    # because the initial person_weight is valid for all persons. However, EMC2
    # does only ask _one_ person per household for trips.. This means that some
    # people are registered with their sociodemographics, but _not_ with the
    # trips. We can identify them by searching for "is_respondent".
    # Now if we simply filter them out, we clearly reduce our weights (because
    # initially they fit EGT and census well). EMC2 already defines weights which
    # are used for the "kish", i.e. the responding persons. At this point they
    # are saved in the data set as trip_weight. Probably it could make sense to
    # give this attribute a more descriptive name in the future.

    # 1) Filter persons for which we have trip information
    df_persons = df_persons[df_persons["number_of_trips"] >= 0].copy()

    # 2) Override weights with the correct weights for the people which have trip information
    df_persons["person_weight"] = df_persons["trip_weight"]

    return df_households, df_persons, df_trips
