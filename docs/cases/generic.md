# Configuration for generic regions

The pipeline makes it easy to create synthetic populations and simulations
for other regions than Île-de-France. In any case, we recommend to first
follow instructions to set up a [synthetic population for Île-de-France](../population.md)
and (if desired) the [respective simulation](../simulation.md). The following
describes the steps and additional data sets necessary to create a population and
simulation for any other French region than Île-de-France.

## Additional data

### A) Buildings database (BD TOPO)

You need to download the region-specific buildings database.

- [Buildings database](https://geoservices.ign.fr/bdtopo)
- In the sidebar on the right, under *Téléchargement anciennes éditions*, click on
  *BD TOPO® 2022 GeoPackage Départements* to go to the saved data publications from 2022.
- The data is split by department and they are identified with a number. Download the dataset
  corresponding to the department you want to simulate.
- Copy the downloaded *7z* files into `data/bdtopo_{name}`.

### B) OpenStreetMap data

Only if you plan to run a simulation (and not just generate a synthetic population),
you need to obtain additional data from OpenStreetMap.
Geofabrik provides a cut-out for any French region:
[Geofabrik](https://download.geofabrik.de/europe/france.html).
Download the region file that you want to simulate in *.osm.pbf* format and put the file into the
folder `data/osm_{name}`.

### C) GTFS data

Again, only if you want to run simulations, the digital transit schedule is required.
GTFS files can be downloaded for most French areas on
[transport.data.gouv.fr](https://transport.data.gouv.fr/datasets?type=public-transit).
Download all the *zip*'s GTFS schedules that you want to use and put them into the folder
`data/gtfs_{name}`.


### D) Adresses database (BAN)

You need to download the region-specific adresses database :

- [Adresses database](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- For each department to simulate, click on the link *adresses-xx.csv.gz* where xx = department code
- Copy the *gz* files into `data/ban_{name}`.


### E) *Optional*: Regional Household Travel Survey

In some regions, a household travel survey specific to the region is available and can be used
instead of the national survey.
The dataset can be obtained either directly from the CEREMA or through the
[ADISP portal](http://www.progedo-adisp.fr/serie_emd.php).

If you have access to a
[EMC2](https://www.cerema.fr/fr/activites/mobilites/connaissance-modelisation-evaluation-mobilite/enquetes-mobilite-emc2)
regional survey (surveys from 2018 or later), put the relevant files into `data/emc2_{name}`.

The following files should be present:

- `data/emc2_{name}/Csv/Fichiers_Standard/xxxxx_men.csv`
- `data/emc2_{name}/Csv/Fichiers_Standard/xxxxx_pers.csv`
- `data/emc2_{name}/Csv/Fichiers_Standard/xxxxx_depl.csv`
- `data/emc2_{name}/Doc/SIG/xxxxx_ZF.[shp/TAB]`

## Generating the population

To generate the synthetic population, the `config.yml` needs to be updated. 
By default the pipeline will filter all other data sets for the
Île-de-France region. To make it use the selected region, adjust the
configuration as follows:

```yaml
config:
  # ...
  regions: []
  departments: ["xx", "yy"] # Replace with all departments codes that you want to simulate.

  ban_path: ban_{name}
  bdtopo_path: bdtopo_{name}
  # ...
```

This will make the pipeline filter all data sets for the departments noted in the list (with the
exception of the national survey ENTD for which all observations are kept since the data is not
representative at the department level).


In case you want to *optionally* use a regional HTS, choose the updated HTS in the config file:

```yaml
config:
  # ...
  hts: emc2
  hts_path: "emc2_{name}"
  # ...
```

Finally, to not confuse output names, we can define a new prefix for the output files:

```yaml
config:
  # ...
  output_prefix: {name}_
  # ...
```

You can now enter your Anaconda environment and call the pipeline with the
`synthesis.output` stage activated. This will generate a synthetic population.

## Running the simulation

To prepare the pipeline for a simulation, the paths to the OSM data sets and to the GTFS schedule
must be adjusted explicitly:

```yaml
config:
  # ...
  gtfs_path: gtfs_{name}
  osm_path: osm_{name}
  # ...
```

Note that the pipeline will automatically cut GTFS and OpenStreetMap data
to the relevant area (defined by the filter above) if you run the simulation.

To test the simulation and generate the relevant MATSim files, run the pipeline
with the `matsim.output` stage enabled.
