# Gathering additional data

In this section we refere to the same data directory structure as described when
gathering the data for the [synthetic population](../population/population_summary.md).

## I) Road network (OpenStreetMap)

The road network in the pipeline is based on OpenStreetMap data.
A cut-out for Île-de-France is available from Geofabrik:

- [Île-de-France OSM](https://download.geofabrik.de/europe/france/ile-de-france.html)
- We recommend to use the fixed snapshot from 01/01/2022: [ile-de-france-220101.osm.pbf](https://download.geofabrik.de/europe/france/ile-de-france-220101.osm.pbf)
- Download *ile-de-france-220101.osm.pbf* and put it into the folder `data/osm_idf`.

## II) Public transit schedule (GTFS)

A digital public transport schedule for Île-de-France is available from Île-de-France mobilités. Since 2023 you are required to create an account and accept the data license before making use of the data.

- Go to [Île-de-France GTFS](https://prim.iledefrance-mobilites.fr/fr/donnees-statiques/offre-horaires-tc-gtfs-idfm)
- Create an account "Connexion" on top of the page
- Once you have created a valid account, go back to the page and click "Exporter la donnée"
- In the popup window, accept the use conditions and select "CSV" type, then click "Télécharger" to download
- The resulting file is not the data itself, but only contains a link to them. Open the downloaded CSV and find the URL starting with `https://data.iledefrance-mobilites.fr/api/v2/catalog/datasets/...`
- Enter the URL in your browser and download the file `IDFM-gtfs.zip`
- Put `IDFM-gtfs.zip` into the folder `data/gtfs_idf`

Note that this schedule is updated regularly and is only valid for the next three
weeks.

## Overview

In your directory structure, there should now be the following additional files:

- `data/osm_idf/ile-de-france-latest.osm.pbf`
- `data/gtfs_idf/IDFM-gtfs.zip`
