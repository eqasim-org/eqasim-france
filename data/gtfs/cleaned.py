import data.gtfs.utils as gtfs
import os, pathlib

"""
This file reads GTFS schedules, cuts them to the scenario area (defined by the
selected regions and departments) and merges them together.
"""

def configure(context):
    context.config("data_path")
    context.config("gtfs_path", "gtfs_idf")

    context.stage("data.spatial.municipalities")

def execute(context):
    input_files = get_input_files("{}/{}".format(context.config("data_path"), context.config("gtfs_path")))
    
    # Prepare bounding area
    df_area = context.stage("data.spatial.municipalities")

    # Load and cut feeds
    feeds = []
    for path in input_files:
        feed = gtfs.read_feed(path)
        feed = gtfs.cut_feed(feed, df_area)

        # This was fixed in pt2matsim, so we can remove one a new release (> 20.7) is available.
        feed = gtfs.despace_stop_ids(feed) # Necessary as MATSim does not like stops/links with spaces

        feeds.append(feed)

    # Merge feeds
    merged_feed = gtfs.merge_feeds(feeds) if len(feeds) > 1 else feeds[0]

    # Fix for pt2matsim (will be fixed after PR #173)
    # Order of week days must be fixed
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    columns = list(merged_feed["calendar"].columns)
    for day in days: columns.remove(day)
    columns += ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    merged_feed["calendar"] = merged_feed["calendar"][columns]

    # Write feed (not as a ZIP, but as files, for pt2matsim)
    gtfs.write_feed(merged_feed, "%s/output" % context.path())

    return "gtfs"

def get_input_files(base_path):
    gtfs_paths = [
        str(child)
        for child in pathlib.Path(base_path).glob("*")
        if child.suffix.lower() == ".zip"
    ]

    if len(gtfs_paths) == 0:
        raise RuntimeError("Did not find any GTFS data (.zip) in {}".format(base_path))
    
    return gtfs_paths

def validate(context):
    input_files = get_input_files("{}/{}".format(context.config("data_path"), context.config("gtfs_path")))
    total_size = 0

    for path in input_files:
        total_size += os.path.getsize(path)

    return total_size
