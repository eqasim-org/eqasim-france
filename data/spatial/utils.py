import shapely.geometry as geo
import numpy as np
import geopandas as gpd
import pandas as pd


def to_gpd(context, df, x="x", y="y", crs="EPSG:2154", column="geometry"):
    df[column] = [
        geo.Point(*coord)
        for coord in context.progress(
            zip(df[x], df[y]), total=len(df), label="Converting coordinates"
        )
    ]
    df = gpd.GeoDataFrame(df, crs="EPSG:2154", geometry=column)

    if not df.crs == "EPSG:2154":
        df = df.to_crs("EPSG:2154")

    return df


def sample_from_shape(shape, count, random, sample_size=None):
    points = []

    if sample_size is None:
        sample_size = int(1.3 * count)

    while len(points) < count:
        minx, miny, maxx, maxy = shape.bounds
        candidates = random.random_sample(size=(sample_size, 2))
        candidates[:, 0] = minx + candidates[:, 0] * (maxx - minx)
        candidates[:, 1] = miny + candidates[:, 1] * (maxy - miny)
        candidates = [geo.Point(*point) for point in candidates]
        candidates = [point for point in candidates if shape.contains(point)]
        points += candidates

    return np.array([(point.x, point.y) for point in points[:count]])


def _sample_from_zones(context, args):
    attribute_value, random_seed = args

    df_zones = context.data("df_zones")
    df = context.data("df")
    attribute = context.data("attribute")

    random = np.random.RandomState(random_seed)
    zone = df_zones[df_zones[attribute] == attribute_value]["geometry"].values[0]

    f = df[attribute] == attribute_value
    coordinates = sample_from_shape(zone, np.count_nonzero(f), random)

    return pd.DataFrame(coordinates, columns=["x", "y"], index=f[f].index)


def sample_from_zones(
    context, df_zones, df, attribute, random, label="Sampling coordinates ..."
):
    assert attribute in df
    assert attribute in df_zones

    unique_values = df[attribute].unique()
    random_seeds = random.randint(0, int(1e6), len(unique_values))

    df_result = []

    with context.parallel(
        dict(df_zones=df_zones, df=df, attribute=attribute)
    ) as parallel:
        for df_partial in context.progress(
            parallel.imap(_sample_from_zones, zip(unique_values, random_seeds)),
            label=label,
            total=len(unique_values),
        ):
            df_result.append(df_partial)

    return pd.concat(df_result)
