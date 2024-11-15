import pandas as pd


def configure(context):
    context.stage("data.od.cleaned")
    context.stage("data.spatial.municipalities")


def execute(context):
    df_codes = context.stage("data.spatial.municipalities")[
        ["commune_id", "departement_id"]
    ]

    result = {}

    for df_data, name in zip(context.stage("data.od.cleaned"), ("work", "education")):
        df_data["origin_id"] = df_data["origin_id"].cat.remove_unused_categories()
        df_data["destination_id"] = df_data[
            "destination_id"
        ].cat.remove_unused_categories()

        df_data = pd.merge(
            df_data,
            df_codes.rename(
                columns={
                    "commune_id": "origin_id",
                    "departement_id": "origin_departement_id",
                }
            ),
            how="left",
            on="origin_id",
        )

        df_data = pd.merge(
            df_data,
            df_codes.rename(
                columns={
                    "commune_id": "destination_id",
                    "departement_id": "destination_departement_id",
                }
            ),
            how="left",
            on="destination_id",
        )

        df_data = df_data[
            ["origin_departement_id", "destination_departement_id", "weight"]
        ].rename(
            columns={
                "origin_departement_id": "home",
                "destination_departement_id": name,
            }
        )

        df_data["home"] = df_data["home"].cat.remove_unused_categories()
        df_data[name] = df_data[name].cat.remove_unused_categories()

        df_data = df_data.groupby(["home", name])["weight"].sum().reset_index()
        result[name] = df_data

    return result
