import zipfile, io
import pandas as pd
import geopandas as gpd
import shapely.geometry as geo
import os
import numpy as np

REQUIRED_SLOTS = [
    "agency", "stops", "routes", "trips", "stop_times"
]

OPTIONAL_SLOTS = [
    "calendar", "calendar_dates", "fare_attributes", "fare_rules",
    "shapes", "frequencies", "transfers", "pathways", "levels",
    "feed_info", "translations", "attributions"
]

def read_feed(path):
    feed = {}

    with zipfile.ZipFile(path, "r") as zip:
        available_slots = zip.namelist()
        prefix = None

        if "agency.txt" in available_slots:
            prefix = ""
        else:
            for slot in available_slots:
                if slot.endswith("agency.txt"):
                    prefix = slot.replace("agency.txt", "")
                    print("Warning: GTFS files seem to be located in: %s" % prefix)
                    break

            if prefix is None:
                raise RuntimeError("No GTFS data found in archive")

        for slot in REQUIRED_SLOTS:
            if not "%s%s.txt" % (prefix, slot) in available_slots:
                raise RuntimeError("Missing GTFS information: %s" % slot)

        if not "%scalendar.txt" % prefix in available_slots and not "%scalendar_dates.txt" % prefix in available_slots:
            raise RuntimeError("At least calendar.txt or calendar_dates.txt must be specified.")

        print("Loading GTFS data from %s ..." % path)

        for slot in REQUIRED_SLOTS + OPTIONAL_SLOTS:
            if "%s%s.txt" % (prefix, slot) in available_slots:
                print("  Loading %s.txt ..." % slot)

                with zip.open("%s%s.txt" % (prefix, slot)) as f:
                    feed[slot] = pd.read_csv(f, skipinitialspace = True)
            else:
                print("  Not loading %s.txt" % slot)

    # Some cleanup

    for slot in ("calendar", "calendar_dates", "trips"):
        if slot in feed and "service_id" in feed[slot] and pd.api.types.is_string_dtype(feed[slot]["service_id"]):
            initial_count = len(feed[slot])
            feed[slot] = feed[slot][feed[slot]["service_id"].str.len() > 0]
            final_count = len(feed[slot])

            if final_count != initial_count:
                print("WARNING Removed %d/%d entries from %s with empty service_id" % (
                    initial_count - final_count, initial_count, slot
                ))

    if "stops" in feed:
        df_stops = feed["stops"]

        if not "parent_station" in df_stops:
            print("WARNING Missing parent_station in stops, setting to NaN")
            df_stops["parent_station"] = np.nan

    if "transfers" in feed:
        df_transfers = feed["transfers"]

        if not "min_transfer_time" in df_transfers:
            df_transfers["min_transfer_time"] = 0

        f = df_transfers["min_transfer_time"].isna()
        if np.any(f):
            print("WARNING NaN numbers for min_transfer_time in transfers")
            df_transfers = df_transfers[~f]

        df_transfers["min_transfer_time"] = df_transfers["min_transfer_time"].astype(int)
        feed["transfers"] = df_transfers

    if "agency" in feed:
        df_agency = feed["agency"]
        df_agency.loc[df_agency["agency_id"].isna(), "agency_id"] = "generic"

    if "routes" in feed:
        df_routes = feed["routes"]
        agency_id = feed["agency"]["agency_id"].values[0]

        if not "agency_id" in df_routes:
            df_routes["agency_id"] = agency_id

        df_routes.loc[df_routes["agency_id"].isna(), "agency_id"] = agency_id

    if "shapes" in feed: del feed["shapes"]
    feed["trips"]["shape_id"] = np.nan

    # Fixes for Nantes PDL
    for item in feed.keys():
        feed[item] = feed[item].drop(columns = [
            c for c in feed[item].columns if c.startswith("ext_")
        ])

    return feed

def write_feed(feed, path):
    print("Writing GTFS data to %s ..." % path)

    if path.endswith(".zip"):
        with zipfile.ZipFile(path, "w") as zip:
            for slot in REQUIRED_SLOTS + OPTIONAL_SLOTS:
                if slot in feed:
                    print("  Writing %s.txt ..." % slot)

                    # We cannot write directly to the file handle as it
                    # is binary, but pandas only writes in text mode.
                    zip.writestr("%s.txt" % slot, feed[slot].to_csv(index = None))

    else:
        if not os.path.exists(path):
            os.mkdir(path)

        if not os.path.isdir(path):
            raise RuntimeError("Should be a directory: %s" % path)

        for slot in REQUIRED_SLOTS + OPTIONAL_SLOTS:
            if slot in feed:
                with open("%s/%s.txt" % (path, slot), "w+", encoding="utf-8") as f:
                    print("  Writing %s.txt ..." % slot)
                    feed[slot].to_csv(f, index = None, lineterminator='\n')

def cut_feed(feed, df_area, crs = None):
    feed = copy_feed(feed)

    df_stops = feed["stops"]

    if "location_type" in df_stops.columns:
        if np.count_nonzero(df_stops["location_type"] == 1) == 0:
            print("Warning! Location types seem to be malformatted. Keeping all stops.")
            df_stations = df_stops.copy()
        else:
            df_stations = df_stops[df_stops["location_type"] == 1].copy()

        df_stations["geometry"] = [
            geo.Point(*xy)
            for xy in zip(df_stations["stop_lon"], df_stations["stop_lat"])
        ]

        df_stations = gpd.GeoDataFrame(df_stations, crs = "EPSG:4326")

        if not crs is None:
            print("Converting stops to custom CRS", crs)
            df_stations = df_stations.to_crs(crs)
        elif not df_area.crs is None:
            print("Converting stops to area CRS", df_area.crs)
            df_stations = df_stations.to_crs(df_area.crs)

        print("Filtering stations ...")
        initial_count = len(df_stations)

        df_stations = gpd.sjoin(df_stations, df_area, predicate = "within")
        final_count = len(df_stations)

        print("Found %d/%d stations inside the specified area" % (final_count, initial_count))
        inside_stations = df_stations["stop_id"]

        # 1) Remove stations that are not inside stations and not have a parent stop
        df_stops = feed["stops"]

        df_stops = df_stops[
            df_stops["parent_station"].isin(inside_stations) |
            (
                df_stops["parent_station"].isna() &
                df_stops["stop_id"].isin(inside_stations)
            )
        ]

    feed["stops"] = df_stops.copy()
    remaining_stops = feed["stops"]["stop_id"].unique()

    # 2) Remove stop times
    df_times = feed["stop_times"]
    df_times = df_times[df_times["stop_id"].astype(str).isin(remaining_stops.astype(str))]
    feed["stop_times"] = df_times.copy()

    # 3) Remove transfers
    if "transfers" in feed:
        df_transfers = feed["transfers"]
        df_transfers = df_transfers[
            df_transfers["from_stop_id"].isin(remaining_stops) &
            df_transfers["to_stop_id"].isin(remaining_stops)
        ]
        feed["transfers"] = df_transfers.copy()

    # 4) Remove pathways
    if "pathways" in feed:
        df_pathways = feed["pathways"]
        df_pathways = df_pathways[
            df_pathways["from_stop_id"].isin(remaining_stops) &
            df_pathways["to_stop_id"].isin(remaining_stops)
        ]
        feed["pathways"] = df_pathways.copy()

    # 5) Remove trips
    trip_counts = feed["stop_times"]["trip_id"].value_counts()
    remaining_trips = trip_counts[trip_counts > 1].index.values

    df_trips = feed["trips"]
    df_trips = df_trips[
        df_trips["trip_id"].isin(remaining_trips)
    ]
    feed["trips"] = df_trips.copy()

    feed["stop_times"] = feed["stop_times"][
        feed["stop_times"]["trip_id"].isin(df_trips["trip_id"].unique())
    ]

    # 6) Remove frequencies
    if "frequencies" in feed:
        df_frequencies = feed["frequencies"]
        df_frequencies = df_frequencies[
            df_frequencies["trip_id"].isin(remaining_trips)
        ]
        feed["frequencies"] = df_frequencies.copy()

    return feed

SLOT_COLLISIONS = [
    { "slot": "agency", "identifier": "agency_id", "references": [
        ("routes", "agency_id"), ("fare_attributes", "agency_id")] },
    { "slot": "stops", "identifier": "stop_id", "references": [
        ("stops", "parent_station"), ("stop_times", "stop_id"),
        ("transfers", "from_stop_id"), ("transfers", "to_stop_id"),
        ("pathways", "from_stop_id"), ("pathways", "to_stop_id")] },
    { "slot": "routes", "identifier": "route_id", "references": [
        ("trips", "route_id"), ("fare_rules", "route_id"),
        ("attributions", "route_id")] },
    { "slot": "trips", "identifier": "trip_id", "references": [
        ("stop_times", "trip_id"), ("frequencies", "trip_id"),
        ("attributions", "trip_id")] },
    { "slot": "calendar", "identifier": "service_id", "references": [
        ("calendar_dates", "service_id"), ("trips", "service_id")] },
    { "slot": "calendar_dates", "identifier": "service_id", "references": [
        ("trips", "service_id"), ("calendar", "service_id")] },
    { "slot": "fare_attributes", "identifier": "fare_id", "references": [
        ("fare_rules", "fare_id")] },
    { "slot": "shapes", "identifier": "shape_id", "references": [
        ("trips", "shape_id")] },
    { "slot": "pathways", "identifier": "pathway_id", "references": [] },
    { "slot": "levels", "identifier": "level_id", "references": [
        ("stops", "level_id")] },
    { "slot": "attributions", "identifier": "attribution_id" },
]

def copy_feed(feed):
    return {
        slot: feed[slot].copy() for slot in feed
    }

def merge_feeds(feeds):
    result = {}

    for k, feed in enumerate(feeds):
        result = merge_two_feeds(result, feed, "_m{}".format(k + 1))

    return result

def merge_two_feeds(first, second, suffix = "_merged"):
    feed = {}

    print("Merging GTFS data ...")

    first = copy_feed(first)
    second = copy_feed(second)

    for collision in SLOT_COLLISIONS:
        if collision["slot"] in first and collision["slot"] in second:
            df_first = first[collision["slot"]]
            df_second = second[collision["slot"]]

            df_first[collision["identifier"]] = df_first[collision["identifier"]].astype(str)
            df_second[collision["identifier"]] = df_second[collision["identifier"]].astype(str)

            df_concat = pd.concat([df_first, df_second], sort = True).drop_duplicates()
            duplicate_ids = list(df_concat[df_concat[collision["identifier"]].duplicated()][
                collision["identifier"]].astype(str).unique())

            if len(duplicate_ids) > 0:
                print("   Found %d duplicate identifiers in %s" % (
                    len(duplicate_ids), collision["slot"]))

                replacement_ids = [str(id) + suffix for id in duplicate_ids]

                df_second[collision["identifier"]] = df_second[collision["identifier"]].replace(
                    duplicate_ids, replacement_ids
                )

                for ref_slot, ref_identifier in collision["references"]:
                    if ref_slot in first and ref_slot in second:
                        first[ref_slot][ref_identifier] = first[ref_slot][ref_identifier].astype(str)
                        second[ref_slot][ref_identifier] = second[ref_slot][ref_identifier].astype(str)

                        second[ref_slot][ref_identifier] = second[ref_slot][ref_identifier].replace(
                            duplicate_ids, replacement_ids
                        )

    for slot in REQUIRED_SLOTS + OPTIONAL_SLOTS:
        if slot in first and slot in second:
            feed[slot] = pd.concat([first[slot], second[slot]], sort = True).drop_duplicates()
        elif slot in first:
            feed[slot] = first[slot].copy()
        elif slot in second:
            feed[slot] = second[slot].copy()

    return feed

def despace_stop_ids(feed, replacement = ":::"):
    feed = copy_feed(feed)

    references = None

    for item in SLOT_COLLISIONS:
        if item["slot"] == "stops":
            references = item["references"]

    df_stops = feed["stops"]
    df_stops["stop_id"] = df_stops["stop_id"].astype(str)

    search_ids = list(df_stops[df_stops["stop_id"].str.contains(" ")]["stop_id"].unique())
    replacement_ids = [item.replace(" ", replacement) for item in search_ids]

    df_stops["stop_id"] = df_stops["stop_id"].replace(search_ids, replacement_ids)

    for reference_slot, reference_field in references:
        if reference_slot in feed:
            feed[reference_slot][reference_field] = feed[reference_slot][reference_field].astype(str).replace(search_ids, replacement_ids)

    print("De-spaced %d/%d stops" % (len(search_ids), len(df_stops)))

    return feed
