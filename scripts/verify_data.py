import requests
import time

# The goal of this script is to verify the availability of the data 
# that is needed to set up the pipeline

sleep_time = 5 # seconds
timeout = 30 # seconds
retries = 3

class Report:
    def __init__(self):
        self.sources = []

    def register(self, name, url):
        self.sources.append({ "name": name, "url": url })

    def validate(self):
        failed = []

        with requests.Session() as session:
            session.headers.update({ "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0" })
            for index, source in enumerate(self.sources):
                print("[{}/{}] Checking {} ...".format(index + 1, len(self.sources), source["name"]))
                
                retry = 0
                success = False

                while not success and retry < retries:
                    try:
                        response = session.head(source["url"], timeout = timeout)
                        source["status"] = response.status_code
                        success = True
                    except TimeoutError:
                        source["status"] = "timeout"
                    except Exception as e:
                        source["status"] = "error"
                        print(e)

                    retry += 1
                    print("  Status {} (retry {}/{})".format(source["status"], retry, retries))
                    
                    time.sleep(sleep_time)

                if source["status"] != 200:
                    failed.append(source["name"])
        
        print("Done.")
        print("Missing: ", len(failed))
        print(failed)

        return len(failed) == 0

report = Report()

report.register(
    "Census data (RP 2019)",
    "https://www.insee.fr/fr/statistiques/fichier/6544333/RP2019_INDCVI_csv.zip"
)

report.register(
    "Population totals (RP 2019)",
    "https://www.insee.fr/fr/statistiques/fichier/6543200/base-ic-evol-struct-pop-2019.zip"
)

report.register(
    "Origin-destination data (RP-MOBPRO 2019)",
    "https://www.insee.fr/fr/statistiques/fichier/6456056/RP2019_mobpro_csv.zip"
)

report.register(
    "Origin-destination data (RP-MOBSCO 2019)",
    "https://www.insee.fr/fr/statistiques/fichier/6456052/RP2019_mobsco_csv.zip"
)

report.register(
    "Income tax data (Filosofi 2019), municipalities",
    "https://www.insee.fr/fr/statistiques/fichier/6036907/indic-struct-distrib-revenu-2019-COMMUNES.zip"
)

report.register(
    "Income tax data (Filosofi 2019), administrative",
    "https://www.insee.fr/fr/statistiques/fichier/6036907/indic-struct-distrib-revenu-2019-SUPRA.zip"
)

report.register(
    "Service and facility census (BPE 2021)",
    "https://www.insee.fr/fr/statistiques/fichier/3568638/bpe21_ensemble_xy_csv.zip"
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
    report.register(
        "National household travel survey (ENTD 2008), {}".format(name),
        "https://www.statistiques.developpement-durable.gouv.fr/media/{}/download?inline".format(identifier)
    )

report.register(
    "IRIS zoning system (2021)",
    "https://data.geopf.fr/telechargement/download/CONTOURS-IRIS/CONTOURS-IRIS_2-1__SHP__FRA_2021-01-01/CONTOURS-IRIS_2-1__SHP__FRA_2021-01-01.7z"
)

report.register(
    "Zoning registry (2021)",
    "https://www.insee.fr/fr/statistiques/fichier/7708995/reference_IRIS_geo2021.zip"
)

report.register(
    "Enterprise census (SIRENE), Etablissement",
    "https://files.data.gouv.fr/insee-sirene/StockEtablissement_utf8.zip"
)

report.register(
    "Enterprise census (SIRENE), Unité Legale",
    "https://files.data.gouv.fr/insee-sirene/StockUniteLegale_utf8.zip"
)

report.register(
    "Enterprise census (SIRENE), Géolocalisé",
    "https://files.data.gouv.fr/insee-sirene-geo/GeolocalisationEtablissement_Sirene_pour_etudes_statistiques_utf8.zip"
)

for department in (75, 77, 78, 91, 92, 93, 94, 95):
    report.register(
        "Buildings database (BD TOPO), {}".format(department),
        "https://data.geopf.fr/telechargement/download/BDTOPO/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D0{}_2022-03-15/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D0{}_2022-03-15.7z".format(department, department)
    )

for department in (75, 77, 78, 91, 92, 93, 94, 95):
    report.register(
        "Adresses database (BAN), {}".format(department),
        "https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/adresses-{}.csv.gz".format(department)
    )

report.register(
    "Population projections",
    "https://www.insee.fr/fr/statistiques/fichier/5894093/00_central.xlsx"
)

report.register(
    "Urban type",
    "https://www.insee.fr/fr/statistiques/fichier/4802589/UU2020_au_01-01-2023.zip"
)

exit(0 if report.validate() else 1)
