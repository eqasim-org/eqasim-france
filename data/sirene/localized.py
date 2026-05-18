import geopandas as gpd

"""
This stage matches the SIRENE enterprise database with INSEE geolocalized auto detected file

Should we consider using location accuracy variable to optimize process?

"""
def configure(context):
    context.stage("data.sirene.cleaned")
    context.stage("data.sirene.raw_geoloc")


def execute(context):
    df_sirene = context.stage("data.sirene.cleaned")
    df_siret_geoloc = context.stage("data.sirene.raw_geoloc")


    # merging geographical SIREN file (containing only SIRET and location) with full SIREN file (all variables and processed)
    df_siret_geoloc.set_index(("siret"),inplace=True,verify_integrity=True)
    df_sirene.set_index(("siret"),inplace=True,verify_integrity=True)
    df_siret_geoloc.sort_index(inplace=True)
    df_sirene.sort_index(inplace=True)

    df_sirene = df_sirene.join(df_siret_geoloc,how="left")
    df_sirene.dropna(subset=['x', 'y'],inplace=True)

    if "epsg" not in df_sirene.columns:
        df_sirene["epsg"] = "2154"

    df_sirene = df_sirene.groupby("epsg")[df_sirene.columns].apply(lambda df: gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x, df.y),
                                                                              crs="EPSG:" + df["epsg"].iloc[0]).to_crs("EPSG:2154"))

    df_sirene = gpd.GeoDataFrame(df_sirene.drop(columns="epsg"), crs="EPSG:2154")
    return df_sirene
