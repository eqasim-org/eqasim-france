import numpy as np
import shapely.geometry as geo
import data.spatial.utils as spatial_utils
import geopandas as gpd

"""
This stage cleans the enterprise census:
  - Filter out enterprises that do not have a valid municipality or IRIS
  - Assign coordinates randomly to enterprises that do not have coordinates
  - Simplify activity types for all enterprises
"""

def configure(context):
    context.stage("data.bpe.raw")

    context.stage("data.spatial.iris")
    context.stage("data.spatial.municipalities")

    context.config("bpe_random_seed", 0)

ACTIVITY_TYPE_MAP = [
    ("A", "other"),         # Police, post office, etc ...
    ("A504", "leisure"),    # Restaurant
    ("B", "shop"),          # Shopping
    ("C", "education"),     # Education
    ("D", "other"),         # Health
    ("E", "other"),         # Transport
    ("F", "leisure"),       # Sports & Culture
    ("G", "other"),         # Tourism, hotels, etc. (Hôtel = G102)
]

def find_outside(context, commune_id):
    df_municipalities = context.data("df_municipalities")
    df = context.data("df")

    df = df[df["commune_id"] == commune_id]
    zone = df_municipalities[df_municipalities["commune_id"] == commune_id]["geometry"].values[0]

    indices = [
        index for index, x, y in df[["x", "y"]].itertuples()
        if not zone.contains(geo.Point(x, y))
    ]

    context.progress.update()
    return indices

def execute(context):
    df = context.stage("data.bpe.raw")

    # Clean IDs
    df["enterprise_id"] = np.arange(len(df))

    # Clean activity type
    df["activity_type"] = "other"
    for prefix, activity_type in ACTIVITY_TYPE_MAP:
        df.loc[df["TYPEQU"].str.startswith(prefix), "activity_type"] = activity_type

    df["activity_type"] = df["activity_type"].astype("category")

    #Add 
    df = df.rename(columns={"TYPEQU":"education_type"})
    df["weight"] = 500 
    # Clean coordinates
    df["x"] = df["LAMBERT_X"].astype(str).str.replace(",", ".").astype(float)
    df["y"] = df["LAMBERT_Y"].astype(str).str.replace(",", ".").astype(float)

    # Clean IRIS and commune
    df["iris_id"] = df["DCIRIS"].str.replace("_", "")
    df["iris_id"] = df["iris_id"].str.replace("IND", "")

    df.loc[df["DEPCOM"] == df["iris_id"], "iris_id"] = "undefined"

    df["iris_id"] = df["iris_id"].astype("category")

    if not "undefined" in df["iris_id"].cat.categories:
        df["iris_id"] = df["iris_id"].cat.add_categories("undefined")

    df["commune_id"] = df["DEPCOM"].astype("category")

    print("Found %d/%d (%.2f%%) observations without IRIS" % (
        (df["iris_id"] == "undefined").sum(), len(df), 100 * (df["iris_id"] == "undefined").mean()
    ))

    # Check whether all communes in BPE are within our set of requested data
    df_municipalities = context.stage("data.spatial.municipalities")
    excess_communes = set(df["commune_id"].unique()) - set(df_municipalities["commune_id"].unique())

    if len(excess_communes) > 0:
        raise RuntimeError("Found additional communes: %s" % excess_communes)

    # We notice that we have some additional IRIS. Make sure they will be placed randomly in there commune later.
    df_iris = context.stage("data.spatial.iris")
    excess_iris = set(df[df["iris_id"] != "undefined"]["iris_id"].unique()) - set(df_iris["iris_id"].unique())
    df.loc[df["iris_id"].isin(excess_iris), "iris_id"] = "undefined"
    print("Excess IRIS without valid code:", excess_iris)

    # Impute missing coordinates for known IRIS
    random = np.random.RandomState(context.config("bpe_random_seed"))

    f_undefined = df["iris_id"] == "undefined"
    f_missing = df["x"].isna()

    print("Found %d/%d (%.2f%%) observations without coordinate" % (
        ((f_missing & ~f_undefined).sum(), len(df), 100 * (f_missing & ~f_undefined).mean()
    )))

    if np.count_nonzero(f_missing & ~f_undefined) > 0:
        # Impute missing coordinates for known IRIS
        df.update(spatial_utils.sample_from_zones(
            context, df_iris, df[f_missing & ~f_undefined], "iris_id", random, label = "Imputing IRIS coordinates ..."))

    if np.count_nonzero(f_missing & f_undefined) > 0:
        # Impute missing coordinates for unknown IRIS
        df.update(spatial_utils.sample_from_zones(
            context, df_municipalities, df[f_missing & f_undefined], "commune_id", random, label = "Imputing municipality coordinates ..."))

    # Consolidate
    df["imputed"] = f_missing
    assert not df["x"].isna().any()

    # Intrestingly, some of the given coordinates are not really inside of
    # the respective municipality. Find them and move them back in.
    outside_indices = []

    with context.progress(label = "Finding outside observations ...", total = len(df["commune_id"].unique())):
        with context.parallel(dict(df = df, df_municipalities = df_municipalities)) as parallel:
            for partial in parallel.imap(find_outside, df["commune_id"].unique()):
                outside_indices += partial

    if len(outside_indices) > 0:
        df.loc[outside_indices, "x"] = np.nan
        df.loc[outside_indices, "y"] = np.nan

        df.update(spatial_utils.sample_from_zones(
            context, df_municipalities, df.loc[outside_indices], "commune_id", random, label = "Fixing outside locations ..."))

        df.loc[outside_indices, "imputed"] = True

    # Package up data set
    df = df[["enterprise_id", "activity_type","education_type", "commune_id", "imputed", "x", "y","weight"]]

    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x, df.y),crs="EPSG:2154")

    return df
