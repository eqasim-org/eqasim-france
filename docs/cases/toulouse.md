# Toulouse / Occitanie

The following page describes the steps and additional data sets necessary to create a population and simulation for **Toulouse**.

## Additional data

### A) Buildings database (BD TOPO)

You need to download the region-specific buildings database.

- [Buildings database](https://geoservices.ign.fr/bdtopo)
- In the sidebar on the right, under *Téléchargement anciennes éditions*, click on *BD TOPO® 2022 GeoPackage Départements* to go to the saved data publications from 2022.
- The data is split by department and they are identified with a number. For the departments around Toulouse, download:
  - Ariège (09)
  - Aude (11)
  - Haute-Garonne (31)
  - Gers (32)
  - Tarn (81)
  - Var (82)
- Copy the six *7z* files into `data/bdtopo_toulouse`.
- If you decide to add additional departments to the simulation (for instance, to simulate the whole Occitanie region) make sure to download the respective data sets.

### B) OpenStreetMap data

Only if you plan to run a simulation (and not just generate a synthetic population),
you need to obtain additional data from OpenStreetMap.
Geofabrik does not provide a continuous cut-out for Occitanie. Instead, the
former regions of [Midi-Pyrennées](https://download.geofabrik.de/europe/france/midi-pyrenees.html) and [Languedoc-Roussilon](https://download.geofabrik.de/europe/france/languedoc-roussillon.html) are available: [midi-pyrenees-220101.osm.pbf](https://download.geofabrik.de/europe/france/midi-pyrenees-220101.osm.pbf) and [languedoc-roussillon-220101.osm.pbf](https://download.geofabrik.de/europe/france/languedoc-roussillon-220101.osm.pbf). Download both regions in *.osm.pbf* format and put the files into the
folder `data/osm_toulouse`.

### C) GTFS data

Again, only if you want to run simulations, the digital transit schedule is required.
Unfortunately, there is no consolidated GTFS schedule avaiable for the Occitanie region. Hence,
it is necessary to collect all relevant GTFS schedules one by one. Here, we
provide a selection of links, which is not necessarily exhaustive:

- [TISSEO (Toulouse)](https://data.toulouse-metropole.fr/explore/dataset/tisseo-gtfs/information/)
- [TAM (Montpellier)](http://data.montpellier3m.fr/dataset/offre-de-transport-tam-en-gtfs)
- [Arc-en-Ciel (Busses Occitanie)](https://www.data.gouv.fr/fr/datasets/offre-de-transport-du-reseau-lio-arc-en-ciel-gtfs/)
- [SNCF TER](https://ressources.data.sncf.com/explore/dataset/sncf-ter-gtfs/information/)
- [SNCF Intercités](https://ressources.data.sncf.com/explore/dataset/sncf-intercites-gtfs/information/)
- [SNCF TGV](https://ressources.data.sncf.com/explore/dataset/horaires-des-train-voyages-tgvinouiouigo/information/)

Download all the *zip*'d GTFS schedules and put them into the folder `data/gtfs_toulouse`.


### D) Adresses database (BAN)

You need to download the region-specific adresses database :

- [Adresses database](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- Click on the link *adresses-xx.csv.gz* where xx = departments codes (09, 11, 31, 32, 81, 82) 
- Copy the *gz* files into `data/ban_toulouse`.

### Overview

Afterwards, you should have the following additional files in your directory structure:

- `data/bdtopo_toulouse/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D009_2022-03-15.7z`
- `data/bdtopo_toulouse/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D011_2022-03-15.7z`
- `data/bdtopo_toulouse/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D031_2022-03-15.7z`
- `data/bdtopo_toulouse/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D032_2022-03-15.7z`
- `data/bdtopo_toulouse/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D081_2022-03-15.7z`
- `data/bdtopo_toulouse/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D082_2022-03-15.7z`
- `data/ban_toulouse/adresses-09.csv.gz`
- `data/ban_toulouse/adresses-11.csv.gz`
- `data/ban_toulouse/adresses-31.csv.gz`
- `data/ban_toulouse/adresses-32.csv.gz`
- `data/ban_toulouse/adresses-81.csv.gz`
- `data/ban_toulouse/adresses-82.csv.gz`

*Only for simulation:*

- `data/osm_toulouse/midi-pyrenees-latest.osm.pbf`
- `data/osm_toulouse/languedoc-roussillon-latest.osm.pbf`
- `data/gtfs_toulouse/tisseo.zip`
- `data/gtfs_toulouse/TAM_MMM_GTFS.zip`
- `data/gtfs_toulouse/RESEAU_LR_GTFS_20200706.zip`
- `data/gtfs_toulouse/export_gtfs_voyages.zip`
- `data/gtfs_toulouse/export-intercites-gtfs-last.zip`
- `data/gtfs_toulouse/export-ter-gtfs-last.zip`

Note that the file names may change slightly over time as GTFS schedule are
updated continuously.

## Generating the population

To generate the synthetic population, the `config.yml` needs to be updated.
By default the pipeline will filter all other data sets for the
Île-de-France region. To make it use the Occitanie region, adjust the
configuration as follows:

```yaml
config:
  # ...
  regions: []
  departments: ["09", "82", "81", "11", "31", "32"] # 12 30 34 46 48 65 66
  # ...
```

This will make the pipeline filter all data sets for the departments noted
in the list above, which is a set of the closest departments around Toulouse.
If you want to generate the whole Occitanie region, add the commented out
department identifiers to the list.

Finally, to not confuse output names, we can define a new prefix for the output files:

```yaml
config:
  # ...
  output_prefix: toulouse_
  # ...
```

You can now enter your Anaconda environment and call the pipeline with the
`synthesis.output` stage activated. This will generate a synthetic population
for Toulouse and surroundings.

## Running the simulation

To prepare the pipeline for a simulation of Toulouse, the paths to the OSM data sets and to the GTFS schedule must be adjusted explicitly:

```yaml
config:
  # ...
  gtfs_path: gtfs_toulouse
  osm_path: osm_toulouse
  ban_path: ban_toulouse
  bdtopo_path: bdtopo_toulouse
  # ...
```

Note that the pipeline will automatically cut GTFS and OpenStreetMap data
to the relevant area (defined by the filter above) if you run the simulation.

To test the simulation and generate the relevant MATSim files, run the pipeline
with the `matsim.output` stage enabled.
