# Population generation cases

The pipeline makes it easy to create synthetic populations and simulations
for other regions than Île-de-France. In any case, we recommend to first
follow instructions to set up a [synthetic population for Île-de-France](../population/population_summary.md)
and (if desired) the [respective simulation](../simulation/simulation_summary.md).

## Generic process

To set up a new region, you need to download the following datasets for the
correct departments or regions:

- [Buildings database (BD TOPO)](https://geoservices.ign.fr/bdtopo)
- [Adresses database (BAN)](https://adresse.data.gouv.fr/data/ban/adresses/latest/csv/)
- [OpenStreetMap data](https://download.geofabrik.de/europe/france.html)
  (when running the simulation only)
- [GTFS data](https://transport.data.gouv.fr/)
  (when running the simulation only)

You have several options for the Household Travel Survey (HTS):

- Use a **national survey** (ENTD or EMP), as described in the
  [Île-de-France case](../population/population_data.md#a-national-household-travel-survey-entd-2008).
- Use a **dedicated implementation for a regional survey**
  (see [specific cases](specific-cases) below).
- Import any regional survey from
  [**MobiSurvStd**](https://mobisurvstd.github.io/MobiSurvStd/surveys.html).

Create or update the configuration file (e.g., `config_myregion.yml`) to
specify the region or departments, data paths, and HTS source.
Below is a template with explanations for each field:

```yaml
config:
  # Define either the regions or departments to be processed.
  # Ensure BD TOPO and BAN files are available in the specified directories.
  regions: []      # List of regions (e.g., ["94"])
  departments: []  # List of departments (e.g., ["01", "38", "42", "69"])

  # Optional: Add a prefix to output files for easy identification.
  output_prefix: myregion_

  # Update paths to region-specific data (relative to `data_path`).
  ban_path: ban_myregion
  bdtopo_path: bdtopo_myregion
  osm_path: osm_myregion
  gtfs_path: gtfs_myregion

  # Define the HTS source: entd, emp, mobisurvstd, or a regional implementation.
  hts: mobisurvstd

  # If using MobiSurvStd, specify the path to the survey zipfile or directory
  # (relative to `data_path`).
  mobisurvstd:
    path: my_survey.zip
```

## Specific cases

For detailed instructions on setting up specific regions, refer to the
following guides:

```{toctree}
:titlesonly:

corsica.md
lyon.md
nantes.md
toulouse.md
```
