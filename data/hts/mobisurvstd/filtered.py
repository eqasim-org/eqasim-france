import polars as pl

import data.hts.hts as hts

"""
This stage filters out observations which live or travel outside of the study area.
"""


def configure(context):
    context.stage("data.hts.mobisurvstd.cleaned")
    context.stage("data.spatial.codes")
    context.config("filter_hts", True)


def execute(context):
    df_households, df_persons, df_trips = context.stage("data.hts.mobisurvstd.cleaned")

    remove_ids = set()

    # Remove persons for which at least 1 trip has NULL departure or arrival time.
    remove_ids |= set(
        df_trips.filter(pl.col("departure_time").is_null() | pl.col("arrival_time").is_null())[
            "person_id"
        ]
    )

    # Remove persons for which at least 1 trip has NULL origin or destination purpose.
    remove_ids |= set(
        df_trips.filter(
            pl.col("preceding_purpose").is_null() | pl.col("following_purpose").is_null()
        )["person_id"]
    )

    # Remove persons for which at least 1 trip has different origin purpose than destination purpose
    # of the previous trip.
    remove_ids |= set(
        df_trips.filter(
            pl.col("preceding_purpose").ne(pl.col("following_purpose").shift(1).over("person_id"))
        )["person_id"]
    )

    if context.config("filter_hts"):
        df_codes = context.stage("data.spatial.codes")
        # Filter for non-residents
        requested_departments = df_codes["departement_id"].astype(str).unique()
        df_persons = df_persons.filter(pl.col("departement_id").is_in(requested_departments))

        # Filter trips outside the area.
        remove_ids |= set(
            df_trips.filter(
                pl.col("origin_departement_id").is_in(requested_departments).not_()
                | pl.col("destination_departement_id").is_in(requested_departments).not_()
            )["person_id"]
        )

    print("Nb persons: {}".format(len(df_persons)))
    # Keep only persons with all their trips and households with at least one remaining person.
    df_persons = df_persons.filter(pl.col("person_id").is_in(remove_ids).not_())
    df_trips = df_trips.filter(pl.col("person_id").is_in(remove_ids).not_())
    df_households = df_households.join(df_persons, on="household_id", how="semi")
    print("Nb persons: {}".format(len(df_persons)))

    df_households_pd = df_households.to_pandas()
    df_persons_pd = df_persons.to_pandas()
    df_trips_pd = df_trips.to_pandas()

    hts.check(df_households_pd, df_persons_pd, df_trips_pd)

    return df_households_pd, df_persons_pd, df_trips_pd
