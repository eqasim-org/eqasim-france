import pandas as pd


def configure(context):
    context.stage("data.spatial.municipalities")


def execute(context):
    df = context.stage("data.spatial.municipalities")
    records = []

    with context.progress(
        total=len(df) ** 2, label="Calculating centroid distances ..."
    ) as progress:
        for origin_id, origin_geometry in zip(df["commune_id"], df["geometry"]):
            for destination_id, destination_geometry in zip(
                df["commune_id"], df["geometry"]
            ):
                records.append(
                    (
                        origin_id,
                        destination_id,
                        origin_geometry.centroid.distance(
                            destination_geometry.centroid
                        ),
                    )
                )
                progress.update()

    return pd.DataFrame.from_records(
        records, columns=["origin_id", "destination_id", "centroid_distance"]
    )
