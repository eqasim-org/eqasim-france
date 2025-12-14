# Running the pipeline

The pipeline code is available in [this repository](https://github.com/eqasim-org/ile-de-france).

## Preparing the project structure

It is best to start with a clean directory sturcture. We recommend the following set-up:

```
/project
  /code (contains the cloned repository)
  /data (contains the raw input data)
  /cache (contains the cache data of the pipeline)
  /output (contains the pipeline output data)
```

Check [Gathering the data](population_data.md) on how to collect the input data that should be placed in `/project/data`.

## Preparing the processing pipeline

To obtain the code, go into the folder `/project` and clone the repository with `git`:

```bash
cd /project
git clone https://github.com/eqasim-org/ile-de-france code
```

which will create the `/project/code` folder containing the pipeline code.

## Preparing the environment

To set up all dependencies, the easiest way is to use `conda` / `mamba`. An open way of setting up such an environment is setting up [miniforge](https://github.com/conda-forge/miniforge). Once it is installed and you are able to call `mamba` from the command line, execute the following code to automatically download all dependencies:

```bash
cd /project/code
mamba env create -f environment.yml -n eqasim
```

It will create a new `mamba` environment called `eqasim`. It, in particular, contains the [synpp](https://github.com/eqasim-org/synpp) package, which is the computational backbone of the pipeline.

:::{tip} 

**Windows:** You can also set up the environment using a graphical user interface for `conda`. You simply need to create a new environment and select `environment.yml` as the dependency definition file.

:::

Whenever you run the processing pipeline, make sure to do so from inside the `eqasim` environment (or whatever name you have given to it). You can enter the environment either though a GUI or by calling

```bash
mamba activate eqasim
```

## Preparing the configuration

Now let's have a look at `config.yml` in `/project/code`. This is likely the only file you will need to modify in case you don't plan to do any development. It contains, in particular, the paths that point to where to find the input data and where to put temporary caching data.

In case you want to learn more about the structure of this configuration file, have a look at the documentation of [synpp](https://github.com/eqasim-org/synpp).

To run the pipeline, open `config.yml` and set the following options. While relative parts with respect to the directory from where you will call the pipeline should work, we recommend setting absolute paths.

- Set `working_directory` to your `/project/cache` directory. The pipeline will create various cache files that will be placed in that directory.
- Set `data_path` in the `config` section to your `/project/data` directory. This is where your input data is located.
- Set `output_path` in the `config` section to your `/project/output` directory. This is where we want the pipeline to create output data for us.

Note that the directories, even if they are empty, must exist before running the pipeline.

## Executing the pipeline

To run the pipeline, go to the `/project/code` directory, enter the `mamba` environment, and call the `synpp` execution script:

```bash
cd /project/code
mamba activate eqasim
python3 -m synpp config.yml
```

A shortcut for running the script when not already inside the environment is to call

```bash
mamba run -n eqasim python3 -m synpp config.yml
```

It will read the configuration file, run the processing pipeline and eventually create the synthetic population inside the output directory.

:::{warning} 

**Windows users:** The cache file paths can get very long and may break the 256 characters limit in the Microsoft Windows OS. In order to avoid any issue make sure the following regitry entry is set to **1**: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled`

You should also set git into *long path mode* by calling: 
`git config --system core.longpaths true`
:::

## Checking the output

After running, you should be able to see a couple of files in the output directory:

- `ile_de_france_meta.json` contains some meta data, e.g. with which random seed or sampling
rate the population was created and when.
- `ile_de_france_persons.csv` and `ile_de_france_households.csv` contain all persons and households in the
population with their respective sociodemographic attributes.
- `ile_de_france_activities.csv` and `ile_de_france_trips.csv` contain all activities and trips in the
daily mobility patterns of these people including attributes on the purposes
of activities.
- `ile_de_france_activities.gpkg` and `ile_de_france_trips.gpkg` represent the same trips and
activities, but in the spatial *GPKG* format. Activities contain point
geometries to indicate where they happen and the trips file contains line
geometries to indicate origin and destination of each trip.
- `ile_de_france_homes.gpkg` contains the places of residence of all households as point geometries.

## Updating the configuration

There are various options that can be changed in the configuration file. To generate a second synthetic population with different settings, it may be useful to add the `output_prefix` option to the `config` section:

```yaml
config:
  output_prefix: my_prefix_
```

All output files will then be prepended by the given prefix instead of the default value `ile_de_france_`.

Note that the `synpp` script allows you to pass any configuration option via the command line, for instance:

```bash
python3 -m synpp config.yml --output_prefix my_prefix_ --output_path /alternative/path
```

In the following, various configuration options will be presented.

### Output format

You may switch from `csv` to `parquet` format by giving a list of desiresd output formats:

```bash
config:
  output_formats: ["csv", "gpkg", "parquet"]
```

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

- To make use of the scaling, [download the projection data from INSEE](https://www.insee.fr/fr/statistiques/7747107?sommaire=6652140). Download *Les tableaux en Excel* which contain all projection scenarios in Excel format. There are various scenarios in Excel format that you can choose from. The default is the *Scénario centrale*, the central scenario. 
- Put the downloaded file into `data/projections`, so you will have the file `data/projections/donnees_detaillees_departementales.zip`

Then, activate the projection procedure by defining the projection scenario and year in the configuration:

```yaml
config: 
  # [...]
  projection_scenario: Central
  projection_year: 2030
```

You may choose any year (past or future) that is contained in the Excel files (sheet *Population*) in the downloaded archive. The same is true for the projection scenarios, which are based on the file names and documented in the Excel files' *Documentation* sheet.

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

### Filter household travel survey data

By default, the pipeline filters out observations from the HTS that correspond to persons living or working outside the configured area (given as departments or regions).
However, the national HTS (ENTD and EMP) may be very sparse in rural and undersampled areas.
The parameters `filter_hts` (default `true`) allows disabling the prefiltering such that the whole set of persons and activity chains is used for generating a regional population when set to `false`:


```yaml
config:
  # [...]
  filter_hts: false
```

For validation, a table of person volumes by age range and trip purpose can be generated from the `analysis.synthesis.population` stage, as explained at the end of this documentation. 


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

For each educational institution, a weight is attributed in the pipeline based on the numbers of students provided in BPE data. The pipeline can also work with a list of educational institution from external geojson or geopackage file with `addresses` as parameter value.
This file must include `education_type`, `commune_id`,`weight`and `geometry` as column with `weight` number of student and `education_type` type of educational institution code similar as BPE ones.

```yaml
config:
  # [...]
  education_location_source: addresses
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

## Enriching person attributes

By default, the pipeline "enriches" generated persons with variables such as
`has_license` and `has_pt_subscription`.
These attributes are derived from the Household Travel Survey (HTS) using
statistical matching.

If you import the HTS using
[MobiSurvStd](../cases/cases_summary.md#generic-process), you can further
enrich person attributes with additional variables.
These variables are specified in the configuration file using the
`extra_enriched_attributes` parameter.

```yaml
config:
  extra_enriched_attributes:
    - "detailed_education_level"
    - "detailed_professional_occupation"
    - "work_only_at_home"
```

For a complete list of possible attributes, refer to the
[MobiSurvStd documentation](https://mobisurvstd.github.io/MobiSurvStd/format/persons.html).
