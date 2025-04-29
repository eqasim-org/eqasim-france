# Lyon

The following page describes the steps and additional data sets necessary to create a population and simulation for **Lyon** and surroundings.

## Additional data

### A) Buildings database (BD TOPO)

You need to download the region-specific buildings database.

- [Buildings database](https://geoservices.ign.fr/bdtopo)
- In the sidebar on the right, under *Téléchargement anciennes éditions*, click on *BD TOPO® 2022 GeoPackage Départements* to go to the saved data publications from 2022.
- The data is split by department and they are identified with a number. For the departments around Lyon, download:
  - Ain (01)
  - Isère (38)
  - Loire (42)
  - Rhône (69)
- Copy the four *7z* files into `data/bdtopo_lyon`.
- If you decide to add additional departments to the simulation (for instance, to simulate the whole Auvergne-Rhône-Alpes region) make sure to download the respective data sets.

### B) OpenStreetMap data

Only if you plan to run a simulation (and not just generate a synthetic population),
you need to obtain additional data from OpenStreetMap.
Geofabrik provides a cut-out for the former [Rhône-Alpes](https://download.geofabrik.de/europe/france/rhone-alpes.html) region: [rhone-alpes-220101.osm.pbf](https://download.geofabrik.de/europe/france/rhone-alpes-220101.osm.pbf). Download the region file in *.osm.pbf* format and put the file into the
folder `data/osm_lyon`.

### C) GTFS data

Again, only if you want to run simulations, the digital transit schedule is required.
Unfortunately, there is no consolidated GTFS schedule avaiable for the region of interest. Hence,
it is necessary to collect all relevant GTFS schedules one by one. Here, we
provide a selection of links, which is not necessarily exhaustive:

- [TCL (Lyon)](https://transport.data.gouv.fr/datasets/horaires-theoriques-du-reseau-transports-en-commun-lyonnais-1/)
- [SNCF TER](https://ressources.data.sncf.com/explore/dataset/sncf-ter-gtfs/information/)
- [SNCF Intercités](https://ressources.data.sncf.com/explore/dataset/sncf-intercites-gtfs/information/)
- [SNCF TGV](https://ressources.data.sncf.com/explore/dataset/horaires-des-train-voyages-tgvinouiouigo/information/)
- [TAG (Grenoble)](https://transport.data.gouv.fr/datasets/horaires-theoriques-du-reseau-tag/)
- [Ruban (Porte d'Isère)](https://transport.data.gouv.fr/datasets/reseau-ruban-donnees-theoriques/)
- [L'va (Vienne)](https://transport.data.gouv.fr/datasets/reseau-lva/?locale=en)
- [STAS (St. Etienne)](https://transport.data.gouv.fr/datasets/donnees-horaires-theoriques-gtfs-du-reseau-de-transport-de-la-metropole-de-saint-etienne-stas/?locale=fr&slug=donnees-horaires-theoriques-gtfs-du-reseau-de-transport-de-la-metropole-de-saint-etienne-stas)
- [Rhône Express](https://transport.data.gouv.fr/datasets/horaires-theoriques-du-service-rhonexpress-de-la-metropole-de-lyon-et-du-departement-du-rhone/)

Download all the *zip*'d GTFS schedules and put them into the folder `data/gtfs_lyon`.


### D) Adresses database (BAN)

You need to download the region-specific adresses database :

- [Adresses database](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- Click on the link *adresses-xx.csv.gz* where xx = departments codes (01,38,42,69) 
- Copy the *gz* files into `data/ban_lyon`.


### E) *Optional*: Regional Household Travel Survey 2015

For Lyon, a regional household travel survey (EDGT Lyon 2015) is available on request
from the authorities. If you have the data available, you can use it in the pipeline.
To do so, put the relevant files into `data/edgt_lyon_2015`.

The data can be obtained either directly from the CEREMA or through the [ADISP portal](http://www.progedo-adisp.fr/serie_emd.php).

#### E.a) Data from CEREMA

If you get the EDGT directly from the CEREMA, the following files should be present:

- `data/edgt_lyon_2015/EDGT-AML-2015_Total_Dessin&Dictionnaire.xls`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.DAT`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.ID`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.IND`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.MAP`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.TAB`
- `data/edgt_lyon_2015/EDGT_AML_DEPLA_DIST_2015-10-27.txt`
- `data/edgt_lyon_2015/EDGT_AML_MENAGE_FAF_TEL_2015-08-03.txt`
- `data/edgt_lyon_2015/EDGT_AML_PERSO_DIST_DT_2015-10-27.txt`
- `data/edgt_lyon_2015/EDGT_AML_TRAJET_DIST_2015-10-27.txt`

#### E.a) Data from the ADISP portal

If you get the EDGT data from the ADISP portal, the following files should be present:

- `data/edgt_lyon_2015/lyon_2015_std_faf_men.csv`
- `data/edgt_lyon_2015/lyon_2015_std_tel_men.csv`
- `data/edgt_lyon_2015/lyon_2015_std_faf_pers.csv`
- `data/edgt_lyon_2015/lyon_2015_std_tel_pers.csv`
- `data/edgt_lyon_2015/lyon_2015_std_faf_traj.csv`
- `data/edgt_lyon_2015/lyon_2015_std_tel_traj.csv`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.DAT`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.ID`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.IND`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.MAP`
- `data/edgt_lyon_2015/EDGT_AML2015_ZF_GT.TAB`



### Overview

Afterwards, you should have the following additional files in your directory structure:

- `data/bdtopo_lyon/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D001_2022-03-15.7z`
- `data/bdtopo_lyon/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D038_2022-03-15.7z`
- `data/bdtopo_lyon/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D042_2022-03-15.7z`
- `data/bdtopo_lyon/BDTOPO_3-0_TOUSTHEMES_GPKG_LAMB93_D069_2022-03-15.7z`
- `data/ban_lyon/adresses-01.csv.gz`
- `data/ban_lyon/adresses-38.csv.gz`
- `data/ban_lyon/adresses-42.csv.gz`
- `data/ban_lyon/adresses-69.csv.gz`

- Plus the files from the EDGT if you want / can use them in `data/edgt_lyon_2015`

*Only for simulation:*

- `data/osm_lyon/rhone-alpes-latest.osm.pbf`
- `data/gtfs_lyon/GTFS_TCL.ZIP`
- `data/gtfs_lyon/CAPI.GTFS.zip`
- `data/gtfs_lyon/GTFS_RX.ZIP`
- `data/gtfs_lyon/SEM-GTFS.zip`
- `data/gtfs_lyon/stas.gtfs.zip`
- `data/gtfs_lyon/VIENNE.GTFS.zip`
- `data/gtfs_lyon/export_gtfs_voyages.zip`
- `data/gtfs_lyon/export-intercites-gtfs-last.zip`
- `data/gtfs_lyon/export-ter-gtfs-last.zip`

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
  departments: ["01", "38", "42", "69"] # 26 "07"
  # ...
```

This will make the pipeline filter all data sets for the departments noted
in the list above, which is a set of the closest departments around Lyon.
If you want to generate the whole (ancient) Rhône-Alpes region, add the commented out
department identifiers to the list (and make sure to download the buildings database)

In case you want to *optionally* use the regional HTS (otherwise the national ENTD)
is used, choose the updated HTS in the config file.

**Important** : when using `edgt_lyon` you **must** set the `edgt_lyon_source` to either `adisp` or `cerema`, else an error will be raised.

```yaml
config:
  # ...
  hts: edgt_lyon
  edgt_lyon_source: adisp  # adisp/cerema
  # ...
```

Finally, to not confuse output names, we can define a new prefix for the output files:

```yaml
config:
  # ...
  output_prefix: lyon_
  # ...
```

You can now enter your Anaconda environment and call the pipeline with the
`synthesis.output` stage activated. This will generate a synthetic population
for Lyon and surroundings.

## Running the simulation

To prepare the pipeline for a simulation of Lyon, the paths to the OSM data sets and to the GTFS schedule must be adjusted explicitly:

```yaml
config:
  # ...
  gtfs_path: gtfs_lyon
  osm_path: osm_lyon
  ban_path: ban_lyon
  bdtopo_path: bdtopo_lyon
  # ...
```

Note that the pipeline will automatically cut GTFS and OpenStreetMap data
to the relevant area (defined by the filter above) if you run the simulation.

To test the simulation and generate the relevant MATSim files, run the pipeline
with the `matsim.output` stage enabled.
