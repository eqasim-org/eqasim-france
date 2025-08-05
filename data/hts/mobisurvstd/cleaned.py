import polars as pl

"""
This stage convert the MobiSurvStd survey to the format expected by eqasim.
"""

# MobiSurvStd mode group -> Eqasim mode
# "pt" is the default mode
# Maybe trips with unknown mode or "other" modes (airplane, boat, etc.) should be dropped instead?
MODE_MAP = {
    "walking": "walk",
    "bicycle": "bike",
    "motorcycle": "car",
    "car_driver": "car",
    "car_passenger": "car_passenger",
    "public_transit": "pt",
    "other": "pt",
    None: "pt",
}

# MobiSurvStd purpose group -> Eqasim purpose
PURPOSE_MAP = {
    "home": "home",
    "work": "work",
    "education": "education",
    "shopping": "shop",
    "task": "other",
    "leisure": "leisure",
    "escort": "other",
    "other": "other",
}


def configure(context):
    context.stage("data.hts.mobisurvstd.raw")

    if context.config("use_urban_type", False):
        context.stage("data.spatial.urban_type")


def execute(context):
    std_survey = context.stage("data.hts.mobisurvstd.raw")

    df_households = std_survey.households.select(
        "household_id",
        household_weight="sample_weight",
        household_size="nb_persons",
        number_of_vehicles=pl.col("nb_cars") + pl.col("nb_motorcycles"),
        number_of_bikes="nb_bicycles",
        departement_id="home_dep",
    )

    df_persons = std_survey.persons.select(
        "person_id",
        "household_id",
        "age",
        sex=pl.when("woman").then(pl.lit("female")).otherwise(pl.lit("male")).cast(pl.Categorical),
        employed=pl.col("professional_occupation") == "worker",
        studies=pl.col("professional_occupation") == "student",
        has_license=pl.col("has_driving_license").eq("yes")
        | pl.col("has_motorcycle_driving_license").eq("yes"),
        has_pt_subscription="has_public_transit_subscription",
        number_of_trips="nb_trips",
        person_weight="sample_weight_all",
        trip_weight="sample_weight_surveyed",
        socioprofessional_class=pl.col("pcs_group_code").fill_null(8),
    )
    if df_persons["person_weight"].is_null().all():
        # For EMP 2019, person weight is unknown, we use trip weight instead (this means that weight
        # will be null for all persons that are not surveyed!).
        df_persons = df_persons.with_columns(person_weight="trip_weight")

    # Only trips on weekdays are considered.
    df_trips = std_survey.trips.filter(
        pl.col("trip_weekday").is_in(("saturday", "sunday")).not_()
    ).select(
        "trip_id",
        "person_id",
        # Convert departure / arrival time from minutes to seconds.
        departure_time=pl.col("departure_time").cast(pl.UInt32) * 60,
        arrival_time=pl.col("arrival_time").cast(pl.UInt32) * 60,
        trip_duration=pl.col("travel_time").cast(pl.UInt32) * 60,
        activity_duration=pl.col("destination_activity_duration").cast(pl.UInt32) * 60,
        preceding_purpose=pl.col("origin_purpose_group").replace_strict(PURPOSE_MAP),
        following_purpose=pl.col("destination_purpose_group").replace_strict(PURPOSE_MAP),
        is_first_trip="first_trip",
        is_last_trip="last_trip",
        mode=pl.col("main_mode_group").replace_strict(MODE_MAP),
        origin_departement_id="origin_dep",
        destination_departement_id="destination_dep",
        # Distance is converted from km to meters.
        euclidean_distance=pl.col("trip_euclidean_distance_km") * 1000.0,
        routed_distance=pl.col("trip_travel_distance_km") * 1000.0,
    )

    # Add households consumption units (1 for 1st person, +0.5 for any other person 14+, +0.3 for
    # any other person below 14.
    # When age is NULL, it is assumed to be over 14.
    cons_units = (
        df_persons.with_columns(over_14=pl.col("age").ge(14).fill_null(True))
        .group_by("household_id")
        .agg(
            consumption_units=1.0
            + pl.max_horizontal(0, pl.col("over_14").sum() - 1) * 0.5
            + pl.col("over_14").not_().sum() * 0.3
        )
    )
    df_households = df_households.join(cons_units, on="household_id", how="left")

    # Add home département to persons.
    df_persons = df_persons.join(
        df_households.select("household_id", "departement_id"), on="household_id", how="left"
    )
    # Flag persons with at least one trip as car passenger.
    df_persons = df_persons.with_columns(
        is_passenger=pl.col("person_id").is_in(
            df_trips.filter(mode="car_passenger")["person_id"].to_list()
        )
    )
    # Add `trip_weight` to trips.
    df_trips = df_trips.join(
        df_persons.select("person_id", "trip_weight"), on="person_id", how="left"
    )

    # Impute urban type.
    if context.config("use_urban_type"):
        df_urban_type = context.stage("data.spatial.urban_type")[["commune_id", "urban_type"]]

        # Add commune_id to persons.
        df_persons = df_persons.join(
            std_survey.households.select("household_id", commune_id="home_insee"),
            on="household_id",
            how="left",
        )
        # Add urban_type to persons.
        df_persons = df_persons.join(pl.from_pandas(df_urban_type), on="commune_id", how="left")
        df_persons = df_persons.with_columns(pl.col("urban_type").fill_null(pl.lit("none"))).drop(
            "commune_id"
        )

    return df_households, df_persons, df_trips
