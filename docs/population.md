# Generating the Île-de-France population

The following sections describe how to generate a synthetic population for
Île-de-France using the pipeline. First all necessary data must be gathered.
Afterwards, the pipeline can be run to create a synthetic population in *CSV*
and *GPKG* format. These outputs can be used for analysis, or serve as input
to [run a transport simulation in MATSim](simulation.md). Also, this guide
is the basis for creating populations and simulations of other regions and
cities such as [Toulouse](cases/toulouse.md) or [Lyon](cases/lyon.md).

This guide will cover the following steps:

- [Gathering the data](#section-data)
- [Running the pipeline](#section-population)
- [Analysing synthetic population](#section-analysis)

## <a name="section-data"></a>Gathering the data

To create the scenario, a couple of data sources must be collected. It is best
to start with an empty folder, e.g. `/data`. All data sets need to be named
in a specific way and put into specific sub-directories. The following paragraphs
describe this process.

### 1) Census data (RP 2019)

Census data containing the socio-demographic information of people living in
France is available from INSEE:

- [Census data](https://www.insee.fr/fr/statistiques/6544333)
- Download the data set in **csv** format by clicking the link under *Individus localisés au canton-ou-ville*.
- Copy the *zip* file into the folder `data/rp_2019`

### 2) Population totals (RP 2019)

We also make use of more aggregated population totals available from INSEE:

- [Population data](https://www.insee.fr/fr/statistiques/6543200)
- Download the data for *France hors Mayotte* in **xlsx** format.
- Copy the *zip* file into the folder `data/rp_2019`.

### 3) Origin-destination data (RP-MOBPRO / RP-MOBSCO 2019)

Origin-destination data is available from INSEE (at two locations):

- [Work origin-destination data](https://www.insee.fr/fr/statistiques/6456056)
- [Education origin-destination data](https://www.insee.fr/fr/statistiques/6456052)
- Download the data from the links, both in **csv** format.
- Copy both *zip* files into the folder `data/rp_2019`.

### 4) Income tax data (Filosofi 2019)

The tax data set is available from INSEE:

- [Income tax data](https://insee.fr/fr/statistiques/6036907)
- Download the munipality data (first link): *Base niveau communes en 2019* in **xlsx** format
- Copy the *zip* file into the folder `data/filosofi_2019`
- Download the administrative level data (second link): *Base niveau administratif en 2019* in **xlsx** format
- Copy the second *zip* file into `data/filosofi_2019`

### 5) Service and facility census (BPE 2021)

The census of services and facilities in France is available from INSEE:

- [Service and facility census](https://www.insee.fr/fr/statistiques/3568638)
- Download the uppermost data set in **csv** format. It contains all available
services while the lower data sets only contain observations for specific sectors.
- Copy the *zip* file into the folder `data/bpe_2021`.

### 6a) National household travel survey (ENTD 2008)

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

### 6b) *(Optional)* Regional household travel survey (EGT)

Usually, you do not have access to the regional household travel
survey, which is not available publicly. In case you have access (but we cannot
guarantee that you have exactly the correct format), you should make sure that
the following files are accessible in the folder `data/egt_2010`:
`Menages_semaine.csv`, `Personnes_semaine.csv`, `Deplacements_semaine.csv`.

### 7) IRIS zoning system (2021)

The IRIS zoning system is available from IGN:

- [IRIS data](https://geoservices.ign.fr/contoursiris)
- Download the **2021** edition.
- Copy the *7z* file into the folder `data/iris_2021`


### 8) Zoning registry (2021)

We make use of a zoning registry by INSEE that establishes a connection between
the identifiers of IRIS, municipalities, departments and regions:

- [Zoning data](https://www.insee.fr/fr/information/7708995)
- Download the **2021** edition as a *zip* file.
- Copy the *zip* file into `data/codes_2021`.

### 9) Enterprise census (SIRENE)

The enterprise census of France is available on data.gouv.fr:

- [Enterprise census](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/)
- Scroll down and click on the blue download button on the right for the two following data sets:
  - **Sirene : Fichier StockUniteLegale** (followed by a date), the database of enterprises
  - **Sirene : Fichier StockEtablissement** (followed by a date), the database of enterprise facilities
- The files are updated monthly and are rather large. After downloading, you should have two files:
  - `StockEtablissement_utf8.zip`
  - `StockUniteLegale_utf8.zip`
- Move both *zip* files into `data/sirene`.

The geolocated enterprise census is available on data.gouv.fr:

- [Geolocated enterprise census](https://www.data.gouv.fr/fr/datasets/geolocalisation-des-etablissements-du-repertoire-sirene-pour-les-etudes-statistiques/)
- Scroll down and click on the blue download button on the right for the following data set:
    - **Sirene : Fichier GeolocalisationEtablissement_Sirene_pour_etudes_statistiques** (followed by a date), 
- Put the downloaded *zip* file into `data/sirene`

### 10) Buildings database (BD TOPO)

The French Buildings database is available from IGN:

- [Buildings database](https://geoservices.ign.fr/bdtopo)
- In the sidebar on the right, under *Téléchargement anciennes éditions*, click on *BD TOPO® 2022 GeoPackage Départements* to go to the saved data publications from 2022.
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

### 11) Adresses database (BAN)

The French adresses database is available on data.gouv.fr :

- [Adresses database](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- Click on the link *adresses-xx.csv.gz* where xx = departments codes (75, 77, 78, 91, 92, 93, 94, 95) 
- Copy the *gz* files into `data/ban_idf`.


### Overview

Your folder structure should now have at least the following files:

- `data/rp_2019/RP2019_INDCVI_csv.zip`
- `data/rp_2019/RP2019_MOBPRO_csv.zip`
- `data/rp_2019/RP2019_MOBSCO_csv.zip`
- `data/rp_2019/base-ic-evol-struct-pop-2019.zip`
- `data/filosofi_2019/indic-struct-distrib-revenu-2019-COMMUNES.zip`
- `data/filosofi_2019/indic-struct-distrib-revenu-2019-SUPRA.zip`
- `data/bpe_2021/bpe21_ensemble_xy_csv.zip`
- `data/entd_2008/Q_individu.csv`
- `data/entd_2008/Q_tcm_individu.csv`
- `data/entd_2008/Q_menage.csv`
- `data/entd_2008/Q_tcm_menage_0.csv`
- `data/entd_2008/K_deploc.csv`
- `data/entd_2008/Q_ind_lieu_teg.csv`
- `data/iris_2021/CONTOURS-IRIS_2-1__SHP__FRA_2021-01-01.7z`
- `data/codes_2021/reference_IRIS_geo2021.zip`
- `data/sirene/StockEtablissement_utf8.csv`
- `data/sirene/StockUniteLegale_utf8.zip`
- `data/sirene/GeolocalisationEtablissement_Sirene_pour_etudes_statistiques_utf8.zip`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D075_2022-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D077_2022-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D078_2022-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D091_2022-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D092_2022-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D093_2022-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D094_2022-03-15.7z`
- `data/bdtopo_idf/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D095_2022-03-15.7z`
- `data/ban_idf/adresses-75.csv.gz`
- `data/ban_idf/adresses-77.csv.gz`
- `data/ban_idf/adresses-78.csv.gz`
- `data/ban_idf/adresses-91.csv.gz`
- `data/ban_idf/adresses-92.csv.gz`
- `data/ban_idf/adresses-93.csv.gz`
- `data/ban_idf/adresses-94.csv.gz`

In case you are using the regional household travel survey (EGT), the following
files should also be in place:

- `data/egt_2010/Menages_semaine.csv`
- `data/egt_2010/Personnes_semaine.csv`
- `data/egt_2010/Deplacements_semaine.csv`

## <a name="section-population">Running the pipeline

The pipeline code is available in [this repository](https://github.com/eqasim-org/ile-de-france).
To use the code, you have to clone the repository with `git`:

```bash
git clone https://github.com/eqasim-org/ile-de-france
```

which will create the `ile-de-france` folder containing the pipeline code. To
set up all dependencies, especially the [synpp](https://github.com/eqasim-org/synpp) package,
which is the code of the pipeline code, we recommend setting up a Python
environment using [Anaconda](https://www.anaconda.com/):

```bash
cd ile-de-france
conda env create -f environment.yml
```

This will create a new Anaconda environment with the name `ile-de-france`.

To activate the environment, run:

```bash
conda activate ile-de-france
```

Now have a look at `config.yml` which is the configuration of the pipeline code.
Have a look at [synpp](https://github.com/eqasim-org/synpp) in case you want to get a more general
understanding of what it does. For the moment, it is important to adjust
two configuration values inside of `config.yml`:

- `working_directory`: This should be an *existing* (ideally empty) folder where
the pipeline will put temporary and cached files during runtime.
- `data_path`: This should be the path to the folder where you were collecting
and arranging all the raw data sets as described above.
- `output_path`: This should be the path to the folder where the output data
of the pipeline should be stored. It must exist and should ideally be empty
for now.
- `output_formats`: This should specify the formats of outputs. Available formats are
csv, gpkg, parquet and geoparquet. Default value is csv and gpkg: ["csv", "gpkg"].

To set up the working/output directory, create, for instance, a `cache` and a
`output` directory. These are already configured in `config.yml`:

```bash
mkdir cache
mkdir output
```

Everything is set now to run the pipeline. The way `config.yml` is configured
it will create the relevant output files in the `output` folder.

To run the pipeline, call the [synpp](https://github.com/eqasim-org/synpp) runner:

```bash
python3 -m synpp
```

It will automatically deshptect the `config.yml`, process all the pipeline code
and eventually create the synthetic population. You should see a couple of
stages running one after another. Most notably, first, the pipeline will read all
the raw data sets to filter them and put them into the correct internal formats.

After running, you should be able to see a couple of files in the `output`
folder:

- `meta.json` contains some meta data, e.g. with which random seed or sampling
rate the population was created and when.
- `persons.csv` and `households.csv` contain all persons and households in the
population with their respective sociodemographic attributes.
- `activities.csv` and `trips.csv` contain all activities and trips in the
daily mobility patterns of these people including attributes on the purposes
of activities.
- `activities.gpkg` and `trips.gpkg` represent the same trips and
activities, but in the spatial *GPKG* format. Activities contain point
geometries to indicate where they happen and the trips file contains line
geometries to indicate origin and destination of each trip.

> [!WARNING]
> Windows users :
> 
> The cache file paths can get very long and may break the 256 characters limit in the Microsoft Windows OS. In order to avoid any issue make sure the following regitry entry is set to **1** : `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled`
> 
> You should also set git into *long path mode* by calling : `git config --system core.longpaths true`



### Mode choice

The synthetic data generated by the pipeine so far does not include transport modes (car, bike, walk, pt, ...) for the individual trips as assigning them consistently is a more computation-heavy process (including routing the individual trips for the modes). To add modes to the trip table, a light-weight MATSim simulation needs to be performed. For that, please configure the additional data requirements as described in the procedure to run a MATSim simulation:

- [Running a MATSim simulation](https://github.com/eqasim-org/ile-de-france/blob/develop/docs/simulation.md)

After that, you can change the `mode_choice` entry in the pipeline configuration file `config.yml` to `true`:

```yaml
config:
  mode_choice: true
```

Running the pipeline again will add the `mode` colum to the `trips.csv` file and its spatial equivalent.

### Population projections

The pipeline allows to make use of population projections from INSEE up to 2070. The same methodology can also be used to scale down the population. The process takes into account the marginal distribution of sex, age, their combination, and the total number of persons. The census data for the base year (see above) is reweighted according to those marginals using *Iterative Proportional Updating*.

- To make use of the scaling, [download the projection data from INSEE](https://www.insee.fr/fr/statistiques/5894093?sommaire=5760764). There are various scenarios in Excel format that you can choose from. The default is the *Scénario centrale*, the central scenario. 
- Put the downloaded file into `data/projection_2021`, so you will have the file `data/projection_2021/00_central.xlsx`

Then, activate the projection procedure by defining the projection year in the configuration:

```yaml
config: 
  # [...]
  projection_year: 2030
```

You may choose any year (past or future) that is contained in the projection scenario Excel file. In case you want to use a different scenario, download the corresponding file, put it into the folder mentioned above, and choose the scenario name via configuration:

```yaml
config: 
  # [...]
  projection_scenario: 00_central
```

### Urban type

The pipeline allows to work with INSEE's urban type classification (unité urbaine) that distinguishes municipalities in *center cities*, *suburbs*, *isolated cities*, and unclassified ones. To impute the data (currently only for some HTS), activate it via the configuration:

```yaml
config:
  # [...]
  use_urban_type: true
```

In order to make use of it for activity chain matching, you can set a custom list of matching attributes like so:

```yaml
config:
  # [...]
  matching_attributes: ["urban_type", "*default*"]
```

The `*default*` trigger will be replaced by the default list of matching attributes.

Note that not all HTS implement the urban type, so matching may not work with some implementations. Most of them, however, contain the data, we just need to update the code to read them in.

To make use of the urban type, the following data is needed:
- [Download the urban type data from INSEE](https://www.insee.fr/fr/information/4802589). The pipeline is currently compatible with the 2023 data set (referencing 2020 boundaries). 
- Put the downloaded *zip* file into `data/urban_type`, so you will have the file `data/urban_type/UU2020_au_01-01-2023.zip`

Then, you should be able to run the pipeline with the configuration explained above.

### Exclude entreprise with no employee

The pipeline allows to exclude all entreprise without any employee (trancheEffectifsEtablissement is NA, "NN" or "00") indicated in Sirene data for working place distribution. It can be activate via this configuration :

```yaml
config:
  # [...]
  exclude_no_employee: true
```

### INSEE 200m tiles data

The pipeline allows to use INSEE 200m tiles data in order to locate population instead of using BAN or BDTOPO data. Population is located in the center of the tiles with the INSEE population weight for each tile.

- In order to use of this location,[download the 200m grid data from INSEE](https://www.insee.fr/fr/statistiques/7655475?sommaire=7655515). The pipeline is currently compatible with 2019 data set.
- Put the downloaded *zip* file into `data/tiles_2019`, so you will have the file `data/tiles_2019/Filosofi2019_carreaux_200m_gpkg.zip`

Then, activate it via the configuration :

```yaml
config:
  # [...]
  home_location_source: tiles
```

This parameter can also activate use of BDTOPO data only or with BAN data to locate population with respectively `building` and `addresses` values.

### Education activities locations

The synthetic data generated by the pipeline so far distribute population to education locations without any distinction of age or type of educational institution.
To avoid to send yound children to high school for example, a matching of educational institution and person by age range can be activated via configuration :

```yaml
config:
  # [...]
  education_location_source: weighted
```

For each type of institution, a weight is attributed by default in the pipeline. To realise a matching weighted with known student numbers by educational institution, the pipeline can also work with a list of educational institution from external geojson or geopackage file with `addresses` as parameter value.
This file must include `TYPEQU`, `commune_id`,`weight`and `geometry` as column with `weight` number of student and `TYPEQU` type of educational institution code similar as BPE ones.

```yaml
config:
  # [...]
  education_location_source: adresses
  education_file: education/education_addresses.geojson
```

### Income

This pipeline allows using the [Bhepop2](https://github.com/tellae/bhepop2) package for income assignation. 

By default, Eqasim infers income from the global income distribution by municipality from the Filosofi data set. 
An income value is drawn from this distribution, independent of the household characteristics. This method is called
`uniform`.

Bhepop2 uses income distributions on subpopulations. For instance, Filosofi provides distributions depending on household size.
Bhepop2 tries to match all the available distributions, instead of just the global one. This results in more
accurate income assignation on subpopulations, but also on the global synthetic population. 
See the [documentation](https://bhepop2.readthedocs.io/en/latest/) for more information on the affectation algorithm.

To use the `bhepop2` method, provide the following config:

```yaml
config:
  income_assignation_method: bhepop2
```

Caution, this method will fail on communes where the Filosofi subpopulation distributions are missing. In this case,
we fall back to the `uniform` method.

## <a name="section-analysis"></a>Analysing synthetic population

In addition to creating synthetic populations, it is possible to output files for analysis.

### Comparison population on grid

Using the comparison_flow_volume pipeline in the Analysis directory, you can generate grids comparing the volumes of two synthetic populations on a grid of 1km² squares for each age group and each purpose of their trips. Like with population creation, the pipeline is run with the [synpp](https://github.com/eqasim-org/synpp) runner and all parameters needed must be included in the `config.yml` file.

To be able to use this pipeline, you must already have create at least one synthetic population (1 for volume visualization and 2 for comparison) and [download France grid from INSEE](https://www.insee.fr/fr/statistiques/fichier/6214726/grille200m_gpkg.zip). From this *zip* file,  you need to extract `grille200m_metropole.gpkg` and put it into `data/grid`.

Then you need to open the `config.yml` and add the `analysis.grid.comparison_flow_volume` stage in the `run` section. To proprely use the comparison_flow_volume pipeline,you'd have to provide the following config:

```yaml
config:
  output_prefix: name_output_studied_
  comparison_file_prefix: name_output_compared_
  analysis_from_file: true
```

Before running it, make sur that populations have same format of file.
After running, you should find all grids for each age group and each trips' purpose in the `output`
folder as: `{output_prefix}_{age group}_{trip pupose}.html`

Note:
With `analysis_from_file` at False, the last synthetic population is studied by default. Also if `output_prefix` and `comparison_file_prefix` refer to the same outputs, or `comparison_file_prefix` is not specified, then only a volume visualisation of this particular population is produced.


### Comparaison population to source data

Using the population pipeline in the Analysis directory, you can generate multiple tables comparing composition of synthetic population to source data. Right now the tables generated compare : population volume by age range, households volume by number of vehicles, population volume with a license and without, trip volume by age range and trip volume by length.
Complementary from the synthetic population only, a table of population volume by age range and trip purpose is also created.

To be able to use this pipeline, you must already have create a synthetic population. Then you need to open the `config.yml` and add the `analysis.synthesis.population` stage in the `run` section. 