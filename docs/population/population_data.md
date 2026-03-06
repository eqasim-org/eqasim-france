# Gathering the data

To create the scenario, synthetic population, a couple of data sources must be collected. It is best to start with an empty folder that can be located anywhere in your file system. In the following, the folder will be denoted as `/data`. All downloaded data sets need to be put into specific sub-directories. The following paragraphs describe this process.

:::{tip} 

**Mixing code and data:** Often, when people clone the eqasim repository, they see the `data` folder and put the data sets there. This is not the intended procedure: the cloned repository only contains the processing code that should be separated from where the data is located. See [Running the pipeline](population_execution.md) for a common project directory structure.

:::

## 1) Census data (RP 2022)

Census data containing the socio-demographic information of people living in
France is available from INSEE:

- [Census data](https://www.insee.fr/fr/statistiques/8647104)
- Download the data set in **parquet** format by clicking the link under *Individus localisés au canton-ou-ville*.
- Copy the *parquet* file into the folder `data/rp_2022`

## 2) Population totals (RP 2022)

We also make use of more aggregated population totals available from INSEE:

- [Population data](https://www.insee.fr/fr/statistiques/8647014)
- Download the data for *France hors Mayotte* in **csv** format.
- Copy the *zip* file into the folder `data/rp_2022`.

## 3) Origin-destination data (RP-MOBPRO / RP-MOBSCO 2022)

Origin-destination data is available from INSEE (at two locations):

- [Work origin-destination data](https://www.insee.fr/fr/statistiques/8589904)
- [Education origin-destination data](https://www.insee.fr/fr/statistiques/8589945)
- Download the data from the links, both in **parquet** format.
- Copy both *parquet* files into the folder `data/rp_2022`.

## 4) Income tax data (Filosofi 2021)

The tax data set is available from INSEE:

- [Income tax data](https://www.insee.fr/fr/statistiques/7756855)
- Download the munipality data (first link): *Base niveau communes en 2021* in **xlsx** format
- Copy the *zip* file into the folder `data/filosofi_2021`
- Download the administrative level data (second link): *Base niveau administratif en 2021* in **xlsx** format
- Copy the second *zip* file into `data/filosofi_2021`

## 5) Service and facility census (BPE 2024)

The census of services and facilities in France is available from INSEE:

- [Service and facility census](https://www.insee.fr/fr/statistiques/8217525)
- Download the data set in **parquet** format.
- Copy the *parquet* file into the folder `data/bpe_2024`.

## 6a) National household travel survey (ENTD 2008)

The national household travel survey is available from the Ministry of Ecology:

- [National household travel survey](https://www.statistiques.developpement-durable.gouv.fr/enquete-nationale-transports-et-deplacements-entd-2008)
- Scroll all the way down the website to the **Table des donnés** (a clickable
pop-down menu).
- You can either download all the available *csv* files in the list, but only
a few are actually relevant for the pipeline. Those are:
  - Données socio-démographiques des ménages (Q_tcm_menage_0.csv)
  - Données socio-démographiques des individus (Q_tcm_individu.csv)
  - Logement, stationnement, véhicules à disposition des ménages (Q_menage.csv)
  - Données trajets domicile-travail, domicile-étude, accidents (Q_individu.csv)
  - Données mobilité contrainte, trajets vers lieu de travail (Q_ind_lieu_teg.csv)
  - Données mobilité déplacements locaux (K_deploc.csv)
- Put the downloaded *csv* files in to the folder `data/entd_2008`.

### 6b) *(Optional)* National Person Mobility Survey (EMP 2019)

The National Person Mobility Survey is also available from the Ministry of Ecology:

- [National Person Mobility Survey](https://www.statistiques.developpement-durable.gouv.fr/resultats-detailles-de-lenquete-mobilite-des-personnes-de-2019)
- Scroll all the way down the website to the **Télécharger les données individuelles anonymisées et leurs dictionnaires** (a clickable pop-down menu).
- Download the data set in **csv** by clicking on the link **Données individuelles anonymisées (fichiers au format CSV) - EMP 2019**
- Copy the *zip* file into the folder `data/emp_2019`.

### 6c) *(Optional)* Regional household travel survey (EGT)

Usually, you do not have access to the regional household travel
survey, which is not available publicly. In case you have access (but we cannot
guarantee that you have exactly the correct format), you should make sure that
the following files are accessible in the folder `data/egt_2010`:
`Menages_semaine.csv`, `Personnes_semaine.csv`, `Deplacements_semaine.csv`.

## 7) IRIS zoning system (2024)

The IRIS zoning system is available from IGN:

- [IRIS data](https://geoservices.ign.fr/contoursiris)
- Download the **2024** edition.
- Copy the *7z* file into the folder `data/iris_2024`


## 8) Zoning registry (2023)

We make use of a zoning registry by INSEE that establishes a connection between
the identifiers of IRIS, municipalities, departments and regions:

- [Zoning data](https://www.insee.fr/fr/information/7708995)
- Download the **2024** edition as a *zip* file.
- Copy the *zip* file into `data/codes_2024`.

## 9) Enterprise census (SIRENE)

The enterprise census of France is available on data.gouv.fr:

- [Enterprise census](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/)
- Scroll down and click on the blue download button on the right for the two following data sets:
  - **Sirene : Fichier StockUniteLegale du dd mm yyyy (format parquet)** (where "dd mm yyyy" is the
    date), the database of enterprises
  - **Sirene : Fichier StockEtablissement du dd mm yyy (format parquet)** (where "dd mm yyyy" is the
    date), the database of enterprise facilities
- The files are updated monthly and are rather large. After downloading, you should have two files:
  - `StockEtablissement_utf8.parquet`
  - `StockUniteLegale_utf8.parquet`
- Move both *parquet* files into `data/sirene`.

The geolocated enterprise census is available on data.gouv.fr:

- [Geolocated enterprise census](https://www.data.gouv.fr/fr/datasets/geolocalisation-des-etablissements-du-repertoire-sirene-pour-les-etudes-statistiques/)
- Scroll down and click on the blue download button on the right for the following data set:
    - **Sirene : Fichier GeolocalisationEtablissement_Sirene_pour_etudes_statistiques du dd mm yyyy
      (format parquet)** (where "dd mm yyyy" is the date)
- Put the downloaded *parquet* file into `data/sirene`

## 10) Buildings database (BD TOPO)

The French Buildings database is available from IGN:

- [Buildings database](https://geoservices.ign.fr/bdtopo)
- In the sidebar on the right, under *Téléchargement anciennes éditions*, click on *BD TOPO® 2024 GeoPackage Départements* to go to the saved data publications from 2024.
- The data is split by department and they are identified with a number. For the Île-de-France region, download:
  - Paris (75)
  - Seine-et-Marne (77)
  - Yvelines (78)
  - Essonne (91)
  - Hauts-de-Seine (92)
  - Seine-Saint-Denis (93)
  - Val-de-Marne (94)
  - Val-d'Oise (95)
- Copy the eight *7z* files into `data/bdtopo_idf`.

## 11) Adresses database (BAN)

The French adresses database is available on data.gouv.fr :

- [Adresses database](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- Click on the link *adresses-xx.csv.gz* where xx = departments codes (75, 77, 78, 91, 92, 93, 94, 95) 
- Copy the *gz* files into `data/ban_idf`.


## Overview

Your folder structure should now have at least the following files:

- `data/rp_2022/RP2022_indcvi.parquet`
- `data/rp_2022/RP2022_mobpro.parquet`
- `data/rp_2022/RP2022_mobsco.parquet`
- `data/rp_2022/base-ic-evol-struct-pop-2022_csv.zip`
- `data/filosofi_2021/indic-struct-distrib-revenu-2021-COMMUNES_XLSX.zip`
- `data/filosofi_2021/indic-struct-distrib-revenu-2021-SUPRA_XLSX.zip`
- `data/bpe_2024/BPE24.parquet`
- `data/entd_2008/Q_individu.csv`
- `data/entd_2008/Q_tcm_individu.csv`
- `data/entd_2008/Q_menage.csv`
- `data/entd_2008/Q_tcm_menage_0.csv`
- `data/entd_2008/K_deploc.csv`
- `data/entd_2008/Q_ind_lieu_teg.csv`
- `data/iris_2024/CONTOURS-IRIS_3-0__GPKG_LAMB93_FXX_2024-01-01.7z`
- `data/codes_2024/reference_IRIS_geo2024.zip`
- `data/sirene/StockEtablissement_utf8.csv`
- `data/sirene/StockUniteLegale_utf8.zip`
- `data/sirene/GeolocalisationEtablissement_Sirene_pour_etudes_statistiques_utf8.zip`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D075_2024-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D077_2024-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D078_2024-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D091_2024-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D092_2024-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D093_2024-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D094_2024-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D095_2024-03-15.7z`
- `data/ban_idf/adresses-75.csv.gz`
- `data/ban_idf/adresses-77.csv.gz`
- `data/ban_idf/adresses-78.csv.gz`
- `data/ban_idf/adresses-91.csv.gz`
- `data/ban_idf/adresses-92.csv.gz`
- `data/ban_idf/adresses-93.csv.gz`
- `data/ban_idf/adresses-94.csv.gz`

In case you are using the National Person Mobility Survey (EMP) or the Regional household travel survey (EGT), the following files should also be respectively in place:
- `data/emp_2019/emp_2019_donnees_individuelles_anonymisees_novembre2024.zip`

or

- `data/egt_2010/Menages_semaine.csv`
- `data/egt_2010/Personnes_semaine.csv`
- `data/egt_2010/Deplacements_semaine.csv`
