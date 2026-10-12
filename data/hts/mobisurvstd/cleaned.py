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
    "task": "task",
    "leisure": "leisure",
    "escort": "escort",
    "other": "other",
    None: "other",
}

def configure(context):
    context.stage("data.hts.mobisurvstd.raw")
    context.config("use_urban_type", False)
    context.config("extra_enriched_attributes", [])


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
        urban_type=pl.col("home_insee_urban_type")
        .cast(pl.String)
        .replace({"outside_urban_unit": "none"})
        .fill_null("none"),
    )

    df_persons = std_survey.persons
    if std_survey.metadata["type"] == "EMP2019":
        # For EMP 2019, persons are asked whether they traveled for the 7 days prior to the
        # interview (variables `traveled_on_{weekday}`), then they are surveyed specifically for one
        # of the day during which they traveled.
        # This means that the original survey has only about 3% of persons with no trip (the persons
        # that did not travel for a full week).
        # To properly represent non-traveling persons, we add, for each weekday, dummy persons with
        # no trip by duplicating the persons with `traveled_on_{weekday} = false`.
        # Then, when filtering a specific weekday, the data will only keep:
        # - The persons surveyed for that weekday (all with trips), with `sample_weight_day` as
        #   weight.
        # - The dummy persons (`traveled_on_{weekday} = false`) with `sample_weight_surveyed` as
        #   weight. This group includes the persons who did not travel for the full week.
        # For these selected persons, the total weight sum up to about 60M, which is roughly the
        # population of France aged 6 or more. The share of persons no traveling is approximately
        # equal to the weighted share of persons with `traveled_on_{weekday} = false`.
        # When filtering multiple weekdays (e.g., all working days), the weights sum to about 60M
        # per selected weekday: shares and per-person averages represent an "average" day of the
        # selected weekdays.
        weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
        # Dummy persons with no trip, for each weekday on which the person did not travel.
        dummies = pl.concat(
            df_persons.filter(pl.col(f"traveled_on_{weekday}").eq(False)).with_columns(
                weekday=pl.lit(weekday, dtype=df_households.schema["trips_weekday"])
            )
            for weekday in weekdays
        )
        # Each dummy person gets a new `person_id` and belongs to a new dummy household (copy of the
        # original household with the dummy's weekday as `trips_weekday`).
        next_person_id = df_persons["person_id"].max() + 1
        next_household_id = df_households["household_id"].max() + 1
        dummies = dummies.with_columns(
            source_household_id=pl.col("household_id"),
            person_id=pl.int_range(
                next_person_id, next_person_id + pl.len(), dtype=df_persons.schema["person_id"]
            ),
            household_id=pl.int_range(
                next_household_id, next_household_id + pl.len(), dtype=df_persons.schema["household_id"]
            ),
            nb_trips=pl.lit(0, dtype=df_persons.schema["nb_trips"]),
        )
        dummy_households = (
            dummies.select("household_id", "source_household_id", trips_weekday="weekday")
            .join(
                df_households.drop("trips_weekday").rename({"household_id": "source_household_id"}),
                on="source_household_id",
                how="left",
                maintain_order="left",
            )
            .select(df_households.columns)
        )
        df_households = pl.concat((df_households, dummy_households))
        # For persons with trip, we need to use `sample_weight_day` as weight.
        df_persons = df_persons.with_columns(sample_weight_surveyed="sample_weight_day")
        df_persons = pl.concat((df_persons, dummies.drop("weekday", "source_household_id")))

    extra_cols = context.config("extra_enriched_attributes")
    assert isinstance(extra_cols, list), "`extra_enriched_attributes` parameter must be a list"
    for col in extra_cols:
        assert col in std_survey.persons.columns, (
            f"Column {col} is not a valid column name for MobiSurvStd persons"
        )

    df_persons = df_persons.select(
        "person_id",
        "household_id",
        "is_surveyed",
        "age",
        "age_class",
        *extra_cols,
        sex=pl.when("woman").then(pl.lit("female")).otherwise(pl.lit("male")).cast(pl.Categorical),
        # Assume that all persons below 5 have studies = True and employed = False (some surveys
        # have NULL values for `professional_occupation`).
        employed=pl.when(pl.col("age") < 5)
        .then(False)
        .otherwise(pl.col("professional_occupation") == "worker")
        # If `professional_occupation` is NULL but a `pcs_group_code` is defined, then assume
        # that the person is working.
        .fill_null(pl.col("pcs_group_code") <= 6)
        .fill_null(False),
        studies=pl.when(pl.col("age") < 5)
        .then(True)
        .otherwise(pl.col("professional_occupation") == "student")
        .fill_null(False),
        professional_activity=pl.col("detailed_professional_occupation")
        .cast(pl.String)
        .replace_strict({
            "worker:full_time": "full_time_worker",
            "worker:part_time": "part_time_worker",
            "worker:unspecified": "full_time_worker",
            "student:primary_or_secondary": "student",
            "student:higher": "student",
            "student:apprenticeship": "full_time_worker",  # Consistent with Census.
            "student:unspecified": "student",
            "other:unemployed": "unemployed",
            "other:retired": "retired",
            "other:homemaker": "homemaker",
            "other:unspecified": "other",
        }),
        has_license=(
            pl.col("has_driving_license").eq_missing("yes")
            | pl.col("has_motorcycle_driving_license").eq_missing("yes")
        ),
        has_pt_subscription=pl.col("has_public_transit_subscription").fill_null(False),
        number_of_trips="nb_trips",
        # In `filtered.py`, only surveyed persons are kept so we use the surveyed weight (this is
        # consistent with the other survey implementations).
        person_weight="sample_weight_surveyed",
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
        .otherwise("pcs_group_code")
        .fill_null(8),
    )
    df_persons = df_persons.with_columns(
        professional_activity=pl.when(pl.col("age") <= 14)
        .then(pl.lit("under14"))
        .otherwise("professional_activity")
    )

    if df_households["trips_weekday"].is_not_null().mean() > 0.95:
        # The weekday at which the trips took place is known (for almost all households): we drop
        # NULL observations.
        df_households = df_households.filter(
            pl.col("trips_weekday").is_not_null()
        ).rename({ "trips_weekday": "weekday" })
    else:
        # There are many NULL values for `trips_weekday` so we keep all observations but the
        # `weekday` variable is not created, which means that the HTS's weekday filter will not be
        # feasible.
        pass

    df_trips = std_survey.trips.select(
        "trip_id",
        "person_id",
        "household_id",
        # Convert departure / arrival time from minutes to seconds.
        departure_time=pl.col("departure_time").cast(pl.UInt32) * 60,
        arrival_time=pl.col("arrival_time").cast(pl.UInt32) * 60,
        trip_duration=pl.col("travel_time").cast(pl.UInt32) * 60,
        activity_duration=pl.col("destination_activity_duration").cast(pl.UInt32) * 60,
        preceding_purpose=pl.col("origin_purpose_group")
        .cast(pl.String)
        .replace_strict(PURPOSE_MAP),
        following_purpose=pl.col("destination_purpose_group")
        .cast(pl.String)
        .replace_strict(PURPOSE_MAP),
        is_first_trip="first_trip",
        is_last_trip="last_trip",
        mode=pl.col("main_mode_group").cast(pl.String).replace_strict(MODE_MAP),
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
    columns = ["household_id", "departement_id"]
    if "weekday" in df_households:
        columns.append("weekday")

    df_persons = df_persons.join(
        df_households.select(columns), on="household_id", how="left"
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
    if not context.config("use_urban_type"):
        df_households = df_households.drop("urban_type")
    return df_households, df_persons, df_trips
