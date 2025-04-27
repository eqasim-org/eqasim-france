
def configure(context):
    context.stage("data.hts.emc2_33.filtered")

def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.emc2_33.filtered")

    # 1) Filter persons for which we don't have trip information
    df_persons = df_persons[df_persons["number_of_trips"] >= 0].copy()

    # 2) Override weights with the correct weights for the people which have trip information
    df_persons["person_weight"] = df_persons["trip_weight"]

    return df_households, df_persons, df_trips
