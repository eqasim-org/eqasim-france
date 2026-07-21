import polars as pl
import numpy as np

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
    context.config("mobisurvstd.weekly", "keep")
    context.config("mobisurvstd.distance", "auto")
    context.config("random_seed")


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

    if df_households["trips_weekday"].is_not_null().mean() > 0.95:
        # The weekday at which the trips took place is known (for almost all households).
        # We select only the households for which the trips were surveyed for a weekday.
        # We also keep the NULL values for `trips_weekday` (for EMP 2019, `trips_weekday`
        # is NULL for persons who did not traveled at all).
        df_households = df_households.filter(
            pl.col("trips_weekday").is_null()
            | pl.col("trips_weekday").is_in(("saturday", "sunday")).not_()
        ).drop("trips_weekday")

    extra_cols = context.config("extra_enriched_attributes")
    assert isinstance(extra_cols, list), "`extra_enriched_attributes` parameter must be a list"
    for col in extra_cols:
        assert col in std_survey.persons.columns, (
            f"Column {col} is not a valid column name for MobiSurvStd persons"
        )

    df_persons = std_survey.persons.select(
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
        .otherwise("pcs_group_code")
        .fill_null(8),
    )
    df_persons = df_persons.with_columns(
        professional_activity=pl.when(pl.col("age") <= 14)
        .then(pl.lit("under14"))
        .otherwise("professional_activity")
    )
    if df_persons["person_weight"].is_null().all():
        # For EMP 2019, person weight is unknown, we use trip weight instead.
        df_persons = df_persons.with_columns(person_weight="trip_weight")

    df_trips = std_survey.trips.select(
        "trip_id",
        "person_id",
        "household_id",
        "trip_weekday",
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
        routed_distance=pl.col("trip_travel_distance_km") * 1000.0,
    )

    # select between euclidean or routed distance
    selected_distance = context.config("mobisurvstd.distance")

    if selected_distance == "auto":
        if df_trips["routed_distance"].is_not_null().mean() > 0.7:
            selected_distance = "routed"
        elif df_trips["euclidean_distance"].is_not_null().mean() > 0.7:
            selected_distance = "euclidean"
        else:
            raise RuntimeError("Neither euclidean nor routed distances are present in the survey")
    
    assert selected_distance in ("routed", "euclidean"), "Unknown distance slot selected"
    
    if selected_distance == "euclidean":
        df_trips = df_trips.drop("routed_distance")
    else:
        df_trips = df_trips.drop("euclidean_distance")

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
    if not context.config("use_urban_type"):
        df_households = df_households.drop("urban_type")

    # handle week-long surveys
    if std_survey.metadata["type"] in ("EMG2023"):
        df_households, df_persons, df_trips = process_week_survey(context, df_households, df_persons, df_trips)

    return df_households, df_persons, df_trips

def process_week_survey(context, df_households, df_persons, df_trips):
    # TODO: Adapt this to polars
    import pandas as pd

    df_households = df_households.to_pandas()
    df_persons = df_persons.to_pandas()
    df_trips = df_trips.to_pandas()

    method = context.config("mobisurvstd.weekly")
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    # at least in EMG23, some people have a repeating day, for instance monday -> ... -> sunday -> monday
    # here we make sure that we always just keep the first weekday
    f = df_trips["trip_weekday"].ne(df_trips["trip_weekday"].shift(1))
    df_trips.loc[f, "day_index"] = np.arange(np.count_nonzero(f))
    df_trips["day_index"] = df_trips["day_index"].ffill().astype(int)

    # drop trips on a duplicate weekday
    df_selector = df_trips.drop_duplicates(["person_id", "trip_weekday"])[["person_id", "day_index"]]
    df_trips = pd.merge(df_trips, df_selector, on = ["person_id", "day_index"])

    if method == "keep":
        # we keep the week structure but extend departure and arrival times
        weekday_index = df_trips["trip_weekday"].apply(weekdays.index).astype(int)
        df_trips["departure_time"] += weekday_index * 24 * 3600
        df_trips["arrival_time"] += weekday_index * 24 * 3600

        # make sure that we start with monday
        df_trips = df_trips.sort_values(by = ["household_id", "person_id", "departure_time"])
        df_trips["trip_id"] = np.arange(len(df_trips)) # reassign for ordering downstream

        # we need to fill the activity duration between the last trip of one day to the next
        f = df_trips["activity_duration"].isna() & df_trips["trip_weekday"].ne(df_trips["trip_weekday"].shift(-1))
        f &= df_trips["person_id"].eq(df_trips["person_id"].shift(-1))
        df_trips.loc[f, "activity_duration"] = df_trips["departure_time"].shift(-1)[f] - df_trips["arrival_time"][f]

    elif method == "sample":
        # we sample a specific weekday for each person
        random = np.random.default_rng(context.config("random_seed") + 5255)
        persons = sorted(df_persons["person_id"].unique())

        # select a random weekday for every person
        df_selection = pd.DataFrame({
            "person_id": persons,
            "trip_weekday": random.choice(weekdays, size = len(persons))
        })

        # reduce the trips to the selected days
        df_trips = pd.merge(df_trips, df_selection, on = ["person_id", "trip_weekday"])

    elif method == "split":
        # we split each person in individual per-day persons and households

        # combination of all households and weekdays
        households = df_households["household_id"].unique()
        df_household_mapping = pd.DataFrame({
            "household_id": np.repeat(households, len(weekdays)),
            "weekday": weekdays * len(households),
        })
        df_household_mapping["updated_household_id"] = np.arange(len(df_household_mapping))

        # duplicate all households per weekday
        df_households = pd.merge(df_households, df_household_mapping, on = "household_id")
        df_households["household_weight"] /= len(weekdays)

        # combination of all persons and weekdays
        persons = df_persons["person_id"].unique()
        df_person_mapping = pd.DataFrame({
            "person_id": np.repeat(persons, len(weekdays)),
            "weekday": weekdays * len(persons),
        })
        df_person_mapping["updated_person_id"] = np.arange(len(df_person_mapping))

        # duplicate all persons per weekday
        df_persons = pd.merge(df_persons, df_person_mapping, on = "person_id")
        df_persons["person_weight"] /= len(weekdays)

        # add updated household id
        df_persons = pd.merge(df_persons, df_household_mapping, on = ["household_id", "weekday"])

        # mapping of ids onto trips
        df_trip_mapping = df_trips[["trip_id", "person_id", "trip_weekday"]].rename(columns = { "trip_weekday": "weekday" })
        df_trip_mapping = pd.merge(df_trip_mapping, 
            df_persons[["person_id", "weekday", "updated_person_id", "updated_household_id"]], 
            on = ["person_id", "weekday"]) # match by person and weekday!

        df_trips = pd.merge(df_trips, df_trip_mapping[["trip_id", "updated_person_id", "updated_household_id"]], on = "trip_id")

        # cleanup
        df_households["household_id"] = df_households["updated_household_id"]
        df_households = df_households.drop(columns = ["updated_household_id"])

        df_persons["household_id"] = df_persons["updated_household_id"]
        df_persons["person_id"] = df_persons["updated_person_id"]
        df_persons = df_persons.drop(columns = ["updated_household_id", "updated_person_id"])

        df_trips["household_id"] = df_trips["updated_household_id"]
        df_trips["person_id"] = df_trips["updated_person_id"]
        df_trips = df_trips.drop(columns = ["updated_household_id", "updated_person_id"])

        # reset weekday column
        df_households["trips_weekday"] = df_households["weekday"]

    else:
        raise RuntimeError("Unknown method for processing week survey: {}".format(method))


    # reset first and last
    df_trips["is_first_trip"] = df_trips["person_id"].ne(df_trips["person_id"].shift(1))
    df_trips["is_last_trip"] = df_trips["person_id"].ne(df_trips["person_id"].shift(-1))

    df_households = pl.DataFrame(df_households)
    df_persons = pl.DataFrame(df_persons)
    df_trips = pl.DataFrame(df_trips)

    return df_households, df_persons, df_trips
