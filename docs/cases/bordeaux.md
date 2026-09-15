# Bordeaux

The pipeline makes it easy to create synthetic populations and simulations
for other regions than Île-de-France. In any case, we recommend to first
follow instructions to set up a [synthetic population for Île-de-France](../population.md)
and (if desired) the [respective simulation](../simulation.md). The following
describes the steps and additional data sets necessary to create a population and
simulation for **Bordeux** and its surrounding department Gironde.

## Additional data

### A) Buildings database (BD TOPO)

You need to download the region-specific buildings database.

- [Buildings database](https://geoservices.ign.fr/bdtopo)
- In the sidebar on the right, under *Téléchargement anciennes éditions*, click on *BD TOPO® 2022 GeoPackage Départements* to go to the saved data publications from 2022.
- The data is split by department and they are identified with a number. For the Gironde department around Bordeaux, download:
  - Gironde (33)
- Copy the *7z* file into `data/bdtopo_bordeaux`.

### B) OpenStreetMap data

Only if you plan to run a simulation (and not just generate a synthetic population),
you need to obtain additional data from OpenStreetMap.
Geofabrik provides a cut-out for the old [Aquitaine](https://download.geofabrik.de/europe/france/aquitaine.html) region: [aquitaine-220101.osm.pbf](https://download.geofabrik.de/europe/france/aquitaine-220101.osm.pbf). Download the region file in *.osm.pbf* format and put the file into the
folder `data/osm_bordeaux`.

### C) GTFS data

Again, only if you want to run simulations, the digital transit schedule is required.
Unfortunately, there is no consolidated GTFS schedule avaiable for the region of interest. Hence,
it is necessary to collect all relevant GTFS schedules one by one. Here, we
provide a selection of links, which is not necessarily exhaustive:

- TODO

Download all the *zip*'d GTFS schedules and put them into the folder `data/gtfs_bordeaux`.

### D) Adresses database (BAN)

You need to download the region-specific adresses database :

- [Adresses database](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- Click on the link *adresses-33.csv.gz*
- Copy the *gz* file into `data/ban_bordeaux`.

### E) *Optional*: Regional Household Travel Survey 2015

For Gironde, a regional household travel survey (EMC2 Gironde 2021) is available as proprietary data that can be obtained from the respective transport and urban planning authorities. The following files should be present:

- `data/emc2_33_2021/08a_EMC2_Gironde_2022_Men_Fusion_men2021_MQPV_23052023.csv`
- `data/emc2_33_2021/07b_EMC2_Gironde_2022_Pers_Fusion_men2021_P19A_13022023.csv`
- `data/emc2_33_2021/07c_EMC2_Gironde_2022_Depl_Fusion_men2021_D11_03022023.csv`

Furthermore, you may want to match activity chains by urban types. In that case, you should also provide the geographic reference file that comes with the survey data:

- `data/emc2_33_2021/spatial/EMC2_Gironde_2022_ZF_160.shp`

### Overview

Afterwards, you should have the following additional files in your directory structure:

- `data/bdtopo_bordeaux/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D033_2022-03-15.7z`
- `data/ban_bordeaux/adresses-33.csv.gz`
- Plus the files from the EMC2 if you want / can use them in `data/emc2_33_2021`

*Only for simulation:*

- `data/osm_bordeaux/aquitaine-latest.osm.pbf`
- `data/gtfs_bordeaux/TODO`
- `data/gtfs_bordeaux/TODO`
- `data/gtfs_bordeaux/TODO`

Note that the file names may change slightly over time as GTFS schedule are
updated continuously.

## Generating the population

To generate the synthetic population, the `config.yml` needs to be updated.
By default the pipeline will filter all other data sets for the
Île-de-France region. To make it use the selected region, adjust the
configuration as follows:

```yaml
config:
  # ...
  regions: []
  departments: [33]
  # ...
```

This will make the pipeline filter all data sets for the department Gironde (33).

In case you want to *optionally* use the regional HTS (otherwise the national ENTD)
is used, choose the updated HTS in the config:

```yaml
config:
  # ...
  hts: emc2_33
  # ...
```

Finally, to not confuse output names, we can define a new prefix for the output files:

```yaml
config:
  # ...
  output_prefix: bordeaux_
  # ...
```

You can now enter your Anaconda environment and call the pipeline with the
`synthesis.output` stage activated. This will generate a synthetic population
for Bordeaux and surroundings.

## Running the simulation

To prepare the pipeline for a simulation of Bordeaux, the paths to the OSM data sets and to the GTFS schedule must be adjusted explicitly:

```yaml
config:
  # ...
  gtfs_path: gtfs_bordeaux
  osm_path: osm_bordeaux
  ban_path: ban_bordeaux
  bdtopo_path: bdtopo_bordeaux
  # ...
```

Note that the pipeline will automatically cut GTFS and OpenStreetMap data
to the relevant area (defined by the filter above) if you run the simulation.

To test the simulation and generate the relevant MATSim files, run the pipeline
with the `matsim.output` stage enabled.
