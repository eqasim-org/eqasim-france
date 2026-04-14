from typing import Annotated
from pathlib import Path

import typer
from rich import print
from rich.progress import Progress
from rich.prompt import Confirm

import os, yaml, requests, sys, shutil

import pandas as pd
import zipfile
import rich

TEMPORARY_PATH = Path(".script_data")
CODES_URL = "https://www.insee.fr/fr/statistiques/fichier/7708995/reference_IRIS_geo2024.zip"

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
                    "DEP": "department_id",
                    "REG": "region_id"
                }).fillna("0")

                df_codes.to_parquet(TEMPORARY_PATH / "codes.parquet")

    return pd.read_parquet(TEMPORARY_PATH / "codes.parquet")

class Registry:
    def __init__(self, data_path: Path):
        self.data_path = data_path
        self.registry = []

    def register(self, name, url, target):
        self.registry.append({ "name": name, "url": url , "target": target})

    def report(self):
        any = False

        for item in self.registry:
            path = self.data_path / item["target"]

            if not path.exists():
                any = True
                print("")
                print("  [bold]{}[/bold]".format(item["name"]))
                print("  URL: {}".format(item["url"]))
                print("  Location: {}".format(item["target"]))

        if any:
            print("")

        return any

    def download(self):
        queue = []

        for item in self.registry:
            path = self.data_path / item["target"]

            if not path.exists():
                queue.append(item)

        for index, item in enumerate(queue):
            os.makedirs(TEMPORARY_PATH, exist_ok = True)
            os.makedirs((self.data_path / item["target"]).parent, exist_ok = True)

            response = requests.get(item["url"], stream = True)
            response.raise_for_status()

            total = int(response.headers.get('content-length', 0))
            if total == 0: total = None

            with Progress() as progress:
                task = progress.add_task("Downloading {}/{} {} ...".format(index + 1, len(queue), item["name"]), total=total)

                with open(TEMPORARY_PATH / "current", "wb+") as file:
                    for chunk in response.iter_content(chunk_size = 8192):
                        if chunk:
                            file.write(chunk)
                            progress.update(task, advance = len(chunk))

                shutil.copy(TEMPORARY_PATH / "current", self.data_path / item["target"])

HELP_CONFIG_PATH = "Path to your config file"

def main(config_path: Annotated[Path, typer.Argument(help = HELP_CONFIG_PATH)]):
    if not os.path.exists(config_path):
        print("[red]Config path does not exist[/red]")
        exit()

    print("Loading input config ...")
    with open(config_path) as f:
        config = yaml.load(f, yaml.FullLoader)

    data_path = Path(config["config"]["data_path"])
    print("Identified data path: {}".format(data_path))

    if not os.path.exists(data_path):
        print("[red]Data path does not exist.[/red]")
    else:
        print("  [green]exists[/green]")

    print("Loading zoning data ...")
    df_codes = load_codes()

    print("Identifying requested departments ...")
    regions = [str(item) for item in config["config"].get("regions", ["11"])]
    departments = [str(item) for item in config["config"].get("departments", [])]
    
    if len(regions) > 0:
        df_codes = df_codes[df_codes["region_id"].isin(regions)]

    if len(departments) > 0:
        df_codes = df_codes[df_codes["department_id"].isin(departments)]
    
    departments = sorted(list(df_codes["department_id"].unique()))
    print("  {}".format(departments))

    if not Confirm.ask("Continue checking missing files?"):
        exit()

    # identify data sets
    registry = Registry(data_path)

    registry.register(
        "Census data (RP 2022)",
        "https://www.insee.fr/fr/statistiques/fichier/8647104/RP2022_indcvi.parquet",
        "rp_2022/RP2022_indcvi.parquet"
    )

    registry.register(
        "Population totals (RP 2022)",
        "https://www.insee.fr/fr/statistiques/fichier/8647014/base-ic-evol-struct-pop-2022_csv.zip",
        "rp_2022/base-ic-evol-struct-pop-2022_csv.zip"
    )

    registry.register(
        "Origin-destination data (RP-MOBPRO 2022)",
        "https://www.insee.fr/fr/statistiques/fichier/8589904/RP2022_mobpro.parquet",
        "rp_2022/RP2022_mobpro.parquet"
    )

    registry.register(
        "Origin-destination data (RP-MOBSCO 2022)",
        "https://www.insee.fr/fr/statistiques/fichier/8589945/RP2022_mobsco.parquet",
        "rp_2022/RP2022_mobsco.parquet"
    )

    registry.register(
        "Income tax data (Filosofi 2021), municipalities",
        "https://www.insee.fr/fr/statistiques/fichier/7756855/indic-struct-distrib-revenu-2021-COMMUNES_XLSX.zip",
        "filosofi_2021/indic-struct-distrib-revenu-2021-COMMUNES_XLSX.zip"
    )

    registry.register(
        "Income tax data (Filosofi 2021), administrative",
        "https://www.insee.fr/fr/statistiques/fichier/7756855/indic-struct-distrib-revenu-2021-SUPRA_XLSX.zip",
        "filosofi_2021/indic-struct-distrib-revenu-2021-SUPRA_XLSX.zip"
    )

    registry.register(
        "Service and facility census (BPE 2024)",
        "https://www.insee.fr/fr/statistiques/fichier/8217525/BPE24.parquet",
        "bpe_2024/BPE24.parquet"
    )

    entd_sources = [
        (2339, "Q_tcm_menage_0"),
        (2555, "Q_tcm_individu"),
        (2556, "Q_menage"),
        (2565, "Q_individu"),
        (2566, "Q_ind_lieu_teg"),
        (2568, "K_deploc")
    ]

    for identifier, name in entd_sources:
        registry.register(
            "National household travel survey (ENTD 2008), {}".format(name),
            "https://www.statistiques.developpement-durable.gouv.fr/media/{}/download?inline".format(identifier),
            "entd_2008/{}.csv".format(name)
        )

    registry.register(
        "IRIS zoning system (2024)",
        "https://data.geopf.fr/telechargement/download/CONTOURS-IRIS/CONTOURS-IRIS_3-0__GPKG_LAMB93_FXX_2024-01-01/CONTOURS-IRIS_3-0__GPKG_LAMB93_FXX_2024-01-01.7z",
        "iris_2024/CONTOURS-IRIS_3-0__GPKG_LAMB93_FXX_2024-01-01.7z"
    )

    registry.register(
        "Zoning registry (2024)",
        "https://www.insee.fr/fr/statistiques/fichier/7708995/reference_IRIS_geo2024.zip",
        "codes_2024/reference_IRIS_geo2024.zip"
    )

    registry.register(
        "Enterprise census (SIRENE), Etablissement",
        "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockEtablissement_utf8.parquet",
        "sirene/StockEtablissement_utf8.parquet"
    )

    registry.register(
        "Enterprise census (SIRENE), Unité Legale",
        "https://object.files.data.gouv.fr/data-pipeline-open/siren/stock/StockUniteLegale_utf8.parquet",
        "sirene/StockUniteLegale_utf8.parquet"
    )

    registry.register(
        "Enterprise census (SIRENE), Géolocalisé",
        "https://object.files.data.gouv.fr/data-pipeline-open/siren/geoloc/GeolocalisationEtablissement_Sirene_pour_etudes_statistiques_utf8.parquet",
        "sirene/GeolocalisationEtablissement_Sirene_pour_etudes_statistiques_utf8.parquet"
    )

    bdtopo_path = config["config"].get("bdtopo_path", "bdtopo_idf")
    for department in (75, 77, 78, 91, 92, 93, 94, 95):
        registry.register(
            "Buildings database (BD TOPO), {}".format(department),
            "https://data.geopf.fr/telechargement/download/BDTOPO/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D0{}_2022-03-15/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D0{}_2022-03-15.7z".format(department, department),
            "{}/BDTOPO_3-5_TOUSTHEMES_GPKG_LAMB93_D0{}_2025-12-15.7z".format(bdtopo_path, department)
        )

    ban_path = config["config"].get("ban_path", "ban_idf")
    for department in (75, 77, 78, 91, 92, 93, 94, 95):
        registry.register(
            "Adresses database (BAN), {}".format(department),
            "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-{}.csv.gz".format(department),
            "{}/adresses-{}.csv.gz".format(ban_path, department)
        )   

    print("Checking the data sets that need to be downloaded ...")
    any = registry.report()
    if any:
        print("[yellow]In case a download aborts, try starting the script again.[/yellow]")
        print("[yellow]Note that for most data sources progress cannot be shown.[/yellow]")

        if not Confirm.ask("Continue downloading data?"):
            exit()
        
        registry.download()

    print("[green]You are up to date![/green]")


if __name__ == "__main__":
    typer.run(main)
