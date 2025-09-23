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
        "trips_weekday",
        household_weight="sample_weight",
        household_size="nb_persons",
        number_of_vehicles=pl.col("nb_cars") + pl.col("nb_motorcycles"),
        number_of_bikes="nb_bicycles",
        departement_id="home_dep",
    )

    if df_households["trips_weekday"].is_not_null().mean() > 0.95:
        # The weekday at which the trips took place is known (for almost all households).
        # We select only the households for which the trips were surveyed for a weekday.
        # We also keep the NULL values for `trips_weekday` (for EMP 2019, `trips_weekday`
        # is NULL for persons who did not traveled at all).
        df_households = df_households.filter(
            pl.col("trips_weekday").is_null()
            | pl.col("trips_weekday").is_in(("saturday", "sunday")).not_()
        ).drop("trips_weekday")

    df_persons = std_survey.persons.select(
        "person_id",
        "household_id",
        "is_surveyed",
        "age",
        "age_class",
        sex=pl.when("woman").then(pl.lit("female")).otherwise(pl.lit("male")).cast(pl.Categorical),
        employed=pl.col("professional_occupation") == "worker",
        studies=pl.col("professional_occupation") == "student",
        # A bit complex expression to do that:
        # driving_license = True, motorcycle_license = True -> True
        # driving_license = True, motorcycle_license = False -> True
        # driving_license = False, motorcycle_license = True -> True
        # driving_license = False, motorcycle_license = False -> False
        # driving_license = True, motorcycle_license = NULL -> True
        # driving_license = False, motorcycle_license = NULL -> False
        # driving_license = NULL, motorcycle_license = True -> True
        # driving_license = NULL, motorcycle_license = False -> NULL
        # driving_license = NULL, motorcycle_license = NULL -> NULL
        has_license=(
            pl.col("has_driving_license").eq("yes")
            | pl.col("has_motorcycle_driving_license").eq_missing("yes")
        ).fill_null(pl.when(pl.col("has_motorcycle_driving_license").eq("yes")).then(True)),
        has_pt_subscription="has_public_transit_subscription",
        number_of_trips="nb_trips",
        person_weight="sample_weight_all",
        trip_weight="sample_weight_surveyed",
        # In MobiSurvStd, variable `pcs_group_code` represents the code of the socioprofessional
        # class (from 1 to 8) but with some differences compared to eqasim:
        # - retired / unemployed can be assigned the code of their former job
        # - students have a NULL value (unless they have a student job or apprenticeship)
        socioprofessional_class=pl.when(
            pl.col("detailed_professional_occupation") == "other:retired"
        )
        .then(7)
        .when(pl.col("professional_occupation") != "worker")
        .then(8)
        .otherwise("pcs_group_code"),
    )
    if df_persons["person_weight"].is_null().all():
        # For EMP 2019, person weight is unknown, we use trip weight instead.
        df_persons = df_persons.with_columns(person_weight="trip_weight")

    df_trips = std_survey.trips.select(
        "trip_id",
        "person_id",
        "household_id",
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
    )

    # Add households consumption units (1 for 1st person, +0.5 for any other person 14+, +0.3 for
    # any other person below 14.
    # When age is NULL but age_class is known, then all minors are considered to be below 14.
    # When both age and age_class are NULL, then all persons are considered to be over 14.
    cons_units = (
        df_persons.with_columns(
            over_14=pl.col("age").ge(14).fill_null(pl.col("age_class") != "17-").fill_null(False)
        )
        .group_by("household_id")
        .agg(
            consumption_units=1.0
            + pl.max_horizontal(0, pl.col("over_14").sum().cast(pl.Int16) - 1) * 0.5
            + pl.col("over_14").not_().sum() * 0.3
        )
    )
    df_households = df_households.join(cons_units, on="household_id", how="left")
    df_persons = df_persons.drop("age_class")

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

    # Drop the persons / trips from households that were dropped earlier.
    df_persons = df_persons.join(df_households, on="household_id", how="semi")
    df_trips = df_trips.join(df_households, on="household_id", how="semi")

    # Impute urban type.
    if context.config("use_urban_type"):
        df_urban_type = context.stage("data.spatial.urban_type")[["commune_id", "urban_type"]]

        # Note that for EMP2019, this will only add null values (home_insee is unknown).
        # Add commune_id to households.
        df_households = df_households.join(
            std_survey.households.select("household_id", commune_id="home_insee"),
            on="household_id",
            how="left",
        )
        # Add urban_type to households.
        df_households = df_households.join(
            pl.from_pandas(df_urban_type), on="commune_id", how="left"
        )
        df_households = df_households.with_columns(
            pl.col("urban_type").fill_null(pl.lit("none"))
        ).drop("commune_id")

    return df_households, df_persons, df_trips
