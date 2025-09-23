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

    # Keep only persons which where surveyed for trips (even if they did not traveled).
    df_persons = df_persons.filter("is_surveyed")

    remove_ids = set()

    # Remove persons for which at least 1 trip has NULL euclidean_distance.
    # Usually, the trips with NULL euclidean_distance are trips that go outside of the survey
    # area and represent only a very small share of the trips.
    remove_ids |= set(df_trips.filter(pl.col("euclidean_distance").is_null())["person_id"])

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
        remove_ids |= set(
            df_persons.filter(
                pl.col("departement_id").is_in(requested_departments, nulls_equal=True).not_()
            )["person_id"]
        )

        # Filter trips outside the area.
        if (
            df_trips["origin_departement_id"].is_not_null().any()
            and df_trips["destination_departement_id"].is_not_null().any()
        ):
            remove_ids |= set(
                df_trips.filter(
                    pl.col("origin_departement_id")
                    .is_in(requested_departments, nulls_equal=True)
                    .not_()
                    | pl.col("destination_departement_id")
                    .is_in(requested_departments, nulls_equal=True)
                    .not_()
                )["person_id"]
            )
        else:
            # For EMP 2019, the origin / destination départements are unknown so we do not apply the
            # filter otherwise all trips would be removed.
            print(
                "Warning. The HTS does not specificy origin / destination departements so the "
                "trips are not filtered for origin / destination inside the requested "
                "departements. Set `filter_hts` to false to silent this warning."
            )

    if remove_ids:
        print(
            (
                "Warning. Dropping {:,} / {:,} persons "
                "(invalid timing, invalid purposes, or invalid origin / destination)"
            ).format(len(remove_ids), len(df_persons))
        )
        # Keep only persons with all their trips and households with at least one remaining person.
        df_persons = df_persons.filter(pl.col("person_id").is_in(remove_ids).not_())
        df_trips = df_trips.filter(pl.col("person_id").is_in(remove_ids).not_())
        df_households = df_households.join(df_persons, on="household_id", how="semi")

        assert len(df_persons), "All persons have been removed from the HTS!"
        assert len(df_trips), "All trips have been removed from the HTS!"

    df_households_pd = df_households.to_pandas()
    df_persons_pd = df_persons.to_pandas()
    df_trips_pd = df_trips.to_pandas()

    hts.check(df_households_pd, df_persons_pd, df_trips_pd)

    return df_households_pd, df_persons_pd, df_trips_pd
