# Nantes

The following page describes the steps and additional data sets necessary to create a population and simulation for **Nantes** and its surrounding department Loire-Atlantique.

## Additional data

### A) Buildings database (BD TOPO)

You need to download the region-specific buildings database.

- [Buildings database](https://geoservices.ign.fr/bdtopo)
- In the sidebar on the right, under *Téléchargement anciennes éditions*, click on *BD TOPO® 2022 GeoPackage Départements* to go to the saved data publications from 2022.
- The data is split by department and they are identified with a number. For the Loire-Atlantique department around Nantes, download:
  - Loire-Atlantique (44)
- Copy the *7z* file into `data/bdtopo_nantes`.

### B) OpenStreetMap data

Only if you plan to run a simulation (and not just generate a synthetic population),
you need to obtain additional data from OpenStreetMap.
Geofabrik provides a cut-out for the [Pays de la Loire](https://download.geofabrik.de/europe/france/pays-de-la-loire.html) region: [pays-de-la-loire-220101.osm.pbf](https://download.geofabrik.de/europe/france/pays-de-la-loire-220101.osm.pbf). Download the region file in *.osm.pbf* format and put the file into the
folder `data/osm_nantes`.

### C) GTFS data

Again, only if you want to run simulations, the digital transit schedule is required.
Unfortunately, there is no consolidated GTFS schedule avaiable for the region of interest. Hence,
it is necessary to collect all relevant GTFS schedules one by one. Here, we
provide a selection of links, which is not necessarily exhaustive:

- [TAN Nantes](https://transport.data.gouv.fr/datasets/tan-arrets-horaires-et-circuits/)
- [Aléop Loire Atlantique](https://transport.data.gouv.fr/datasets/arrets-horaires-et-circuits-des-lignes-de-transports-aleop-1)
- [STRAN Saint-Nazaire](https://transport.data.gouv.fr/datasets/stran-arrets-horaires-et-circuits-urbains-et-scolaires-gtfs/)
- [Brévibus](https://transport.data.gouv.fr/datasets/reseau-urbain-brevibus/) (save as `brevibus.gtfs.zip`)
- [Guérande](https://transport.data.gouv.fr/datasets/lignes-arrets-et-horaires-de-transport-pour-cap-atlantique-lila-presquile-gtfs/)
- [SNCF TER](https://ressources.data.sncf.com/explore/dataset/sncf-ter-gtfs/information/)
- [SNCF Intercités](https://ressources.data.sncf.com/explore/dataset/sncf-intercites-gtfs/information/)
- [SNCF TGV](https://ressources.data.sncf.com/explore/dataset/horaires-des-train-voyages-tgvinouiouigo/information/)

Download all the *zip*'d GTFS schedules and put them into the folder `data/gtfs_nantes`.

### D) Adresses database (BAN)

You need to download the region-specific adresses database :

- [Adresses database](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- Click on the link *adresses-44.csv.gz*
- Copy the *gz* file into `data/ban_nantes`.

### E) *Optional*: Regional Household Travel Survey 2015

For Loire Atlantique, a regional household travel survey (EDGT Loire Atlantique 2015) is available as [open data](https://data.loire-atlantique.fr/explore/dataset/224400028_enquete-deplacements-en-loire-atlantique/information/). Download the raw data "données brutes" at bullet point 1 one the website. Put the relevant files into `data/edgt_44_2015`. The following files
should be present:

- `data/edgt_44_2015/02a_EDGT_44_MENAGE_FAF_TEL_2015-08-07_modifZF.txt`
- `data/edgt_44_2015/02b_EDGT_44_PERSO_FAF_TEL_ModifPCS_2016-04-14.txt`
- `data/edgt_44_2015/02c_EDGT_44_DEPLA_FAF_TEL_DIST_2015-11-10.txt`

### Overview

Afterwards, you should have the following additional files in your directory structure:

- `data/bdtopo_nantes/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D044_2022-03-15.7z`
- `data/ban_nantes/adresses-44.csv.gz`
- Plus the files from the EDGT if you want / can use them in `data/edgt_44_2015`

*Only for simulation:*

- `data/osm_nantes/pays-de-la-loire-latest.osm.pbf`
- `data/gtfs_nantes/gtfs-tan.zip`
- `data/gtfs_nantes/pdl44.zip`
- `data/gtfs_nantes/stran-merge.gtfs.zip`
- `data/gtfs_nantes/brevibus.gtfs.zipp`
- `data/gtfs_nantes/lilapresquile.gtfs.zip`
- `data/gtfs_nantes/export-ter-gtfs-last.zip`
- `data/gtfs_nantes/export_gtfs_voyages.zip`
- `data/gtfs_nantes/export-intercites-gtfs-last.zip`

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
  departments: [44]
  # ...
```

This will make the pipeline filter all data sets for the department Loire Atlantique (44).

In case you want to *optionally* use the regional HTS (otherwise the national ENTD)
is used, choose the updated HTS in the config:

```yaml
config:
  # ...
  hts: edgt_44
  # ...
```

Finally, to not confuse output names, we can define a new prefix for the output files:

```yaml
config:
  # ...
  output_prefix: nantes_
  # ...
```

You can now enter your Anaconda environment and call the pipeline with the
`synthesis.output` stage activated. This will generate a synthetic population
for Nantes and surroundings.

## Running the simulation

To prepare the pipeline for a simulation of Nantes, the paths to the OSM data sets and to the GTFS schedule must be adjusted explicitly:

```yaml
config:
  # ...
  gtfs_path: gtfs_nantes
  osm_path: osm_nantes
  ban_path: ban_nantes
  bdtopo_path: bdtopo_nantes
  # ...
```

Note that the pipeline will automatically cut GTFS and OpenStreetMap data
to the relevant area (defined by the filter above) if you run the simulation.

To test the simulation and generate the relevant MATSim files, run the pipeline
with the `matsim.output` stage enabled.
