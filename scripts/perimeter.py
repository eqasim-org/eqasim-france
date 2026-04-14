from typing import Annotated, Literal
import typer
from rich import print
from rich.progress import Progress
from pathlib import Path
import yaml
import os
import pandas as pd
import geopandas as gpd
import py7zr, zipfile
import requests

IRIS_URL = "https://data.geopf.fr/telechargement/download/CONTOURS-IRIS/CONTOURS-IRIS_3-0__GPKG_LAMB93_FXX_2024-01-01/CONTOURS-IRIS_3-0__GPKG_LAMB93_FXX_2024-01-01.7z"
CODES_URL = "https://www.insee.fr/fr/statistiques/fichier/7708995/reference_IRIS_geo2024.zip"

TEMPORARY_PATH = Path(".script_data")

HELP_INPUT_PATH = "The path to your original config.yml (input)"
HELP_OUTPUT_PATH = "The path to the updated config.yml (output)"
HELP_PERIMETER_PATH = "The path to a geograpic file containing the perimeter of your use case (input)"

def load_iris():
    if not os.path.exists(TEMPORARY_PATH / "iris.7z"):
        os.makedirs(TEMPORARY_PATH, exist_ok = True)

        print("Downloading IRIS database from IGN ...")
        response = requests.get(IRIS_URL, stream = True)
        response.raise_for_status()

        total = int(response.headers.get('content-length', 0))
        with Progress() as progress:
            task = progress.add_task("Downloading ...", total=total)

            with open(TEMPORARY_PATH / "iris.7z", "wb+") as file:
                for chunk in response.iter_content(chunk_size = 8192):
                    if chunk:
                        file.write(chunk)
                        progress.update(task, advance = len(chunk))
        
    if not os.path.exists(TEMPORARY_PATH / "iris.gpkg"):
        with py7zr.SevenZipFile(TEMPORARY_PATH / "iris.7z") as archive:
            contour_paths = [
                path for path in archive.getnames()
                if "LAMB93" in path
            ]

            archive.extract(TEMPORARY_PATH, contour_paths)
        
        gpkg_path = [path for path in contour_paths if path.endswith(".gpkg")]
        
        if len(gpkg_path) != 1:
            print("[red]Cannot find IRIS shapes in the downloaded archive[/red]")
            exit()

        df_iris = gpd.read_file(TEMPORARY_PATH / gpkg_path[0], dtype={"code_iris":str,"code_insee":str})[[
            "code_insee", "code_iris", "geometry"
        ]].rename(columns = {
            "code_iris": "iris_id",
            "code_insee": "municipality_id"
        })

        df_iris["department_id"] = df_iris["municipality_id"].str[:2]

        df_iris.to_file(TEMPORARY_PATH / "iris.gpkg")
    
    return gpd.read_file(TEMPORARY_PATH / "iris.gpkg")

def load_codes():
    if not os.path.exists(TEMPORARY_PATH / "codes.zip"):
        os.makedirs(TEMPORARY_PATH, exist_ok = True)

        print("Downloading zoning codes from INSEE ...")
        response = requests.get(CODES_URL, stream = True)
        response.raise_for_status()

        total = int(response.headers.get('content-length', 0))
        with Progress() as progress:
            task = progress.add_task("Downloading ...", total=total)

            with open(TEMPORARY_PATH / "codes.zip", "wb+") as file:
                for chunk in response.iter_content(chunk_size = 8192):
                    if chunk:
                        file.write(chunk)
                        progress.update(task, advance = len(chunk))
        
    if not os.path.exists(TEMPORARY_PATH / "codes.parquet"):
        with zipfile.ZipFile(TEMPORARY_PATH / "codes.zip") as archive:
            with archive.open("reference_IRIS_geo2024.xlsx") as f:
                df_codes = pd.read_excel(f,
                    skiprows = 5, sheet_name = "Emboitements_IRIS",dtype={"CODE_IRIS":str,"DEPCOM":str,"REG":str}
                )[["CODE_IRIS", "DEPCOM", "DEP", "REG"]].rename(columns = {
                    "CODE_IRIS": "iris_id",
                    "DEPCOM": "commune_id",
                    "DEP": "departement_id",
                    "REG": "region_id"
                }).fillna("0")

                df_codes.to_parquet(TEMPORARY_PATH / "codes.parquet")

    return pd.read_parquet(TEMPORARY_PATH / "codes.parquet")

def main(
        perimeter_path: Annotated[Path, typer.Argument(help = HELP_PERIMETER_PATH)],
        input_path: Annotated[Path, typer.Option(help = HELP_INPUT_PATH)] = None, 
        output_path: Annotated[Path, typer.Option(help = HELP_OUTPUT_PATH)] = None,
        level: Annotated[Literal["department", "region"], typer.Option()] = "department"):
    if bool(input_path) ^ bool(output_path):
        print("[red]Both input and output path need to be given if you want to adjust a config file")
        exit()

    if input_path:
        if not os.path.exists(input_path):
            print("[red]Input path does not exist[/red]")
            exit()

    if not os.path.exists(perimeter_path):
        print("[red]Perimeter file does not exist[/red]")
        exit()

    print("Loading perimeter ...")
    df_perimeter = gpd.read_file(perimeter_path).to_crs("EPSG:2154")

    print("Loading IRIS data ...")
    df_iris = load_iris()

    print("Loading zoning codes ...")
    df_codes = load_codes()

    print("Finding intersecting areas with perimeter ...")
    df_selection = gpd.sjoin(df_iris, df_perimeter)
    df_selection = pd.merge(df_selection, df_codes, on = "iris_id")

    regions = sorted(list(df_selection["region_id"].unique()))
    departments = sorted(list(df_selection["department_id"].unique()))
    municipalities = sorted(list(df_selection["municipality_id"].unique()))

    print("  Found {} IRIS".format(len(df_selection)))
    print("  Found {} municipalities".format(len(municipalities)))
    print("  Found {} departments".format(len(departments)))
    print("  Found {} regions".format(len(regions)))

    print("[bold]Add the following to your config.yml[/bold]:")

    if level == "region":
        print("  regions: {}".format(regions))
    else:
        print("  regions: []")
        print("  departments: {}".format(departments))

    if input_path:
        print("Loading input config ...")
        with open(input_path) as f:
            config = yaml.load(f, yaml.FullLoader)

        print("Updating the config ...")

        if level == "region":
            config["config"]["regions"] = regions
        else:
            config["config"]["regions"] = []
            config["config"]["departments"] = departments

        print("Writing updated config ...")
        with open(output_path, "w+") as f:
            yaml.dump(config, f)

        print("[green]Done![/green]")

if __name__ == "__main__":
    typer.run(main)
