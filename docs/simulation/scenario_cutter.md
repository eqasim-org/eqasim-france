# Scenario Cutter

The Scenario Cutter allows you to define and use a specific region of interest, such as a city or metropolitan area area for further detailed simulation or analysis. This is by providing a custom boundary (cutter) file.

The code is called from the [eqasim-java](https://github.com/eqasim-org/eqasim-java) project, here: [RunScenarioCutter.java](https://github.com/eqasim-org/eqasim-java/blob/develop/core/src/main/java/org/eqasim/core/scenario/cutter/RunScenarioCutter.java). 

## Configuration Options

The cutter is configured through the `config` section of your YAML configuration file. The following options are available:

- **`cutter_path`**: (default: `cutter`)
  - The relative path (from your `data_path`) to the directory containing the cutter file.
  - Example: `cutter_path: cutter`

- **`cutter_file`**: (default: `cutter.geojson`)
  - The name of the file (usually a GeoJSON) that defines the area to be used as a cutter.
  - Example: `cutter_file: cutter.geojson`

- **`cutter_name`**: (optional)
  - A label for the cutter area, used for output file naming and documentation.
  - Example: `cutter_name: paris`

- **`cutter_after_full_simulation`**: (optional, default: `False`)
  - If set to `True`, the cutter will be applied after the full simulation is run, rather than before.
  - Example: `cutter_after_full_simulation: True`

### Example Configuration

```yaml

run:
  - matsim.simulation.cutter.cut
  # - matsim.simulation.cutter.full_run

config:
  data_path: /path/to/my/data
  cutter_path: cutter
  cutter_file: cutter.geojson
  cutter_name: paris
  cutter_after_full_simulation: False
```

## How It Works

- The cutter module loads the specified GeoJSON file from the directory defined by `data_path` and `cutter_path`.
- The geometry in this file is used to select or mask the area of interest for the simulation.
- If `cutter_after_full_simulation` is enabled, the full simulation is run first, and then the results are filtered to the cutter area.

## Requirements
- The cutter file must be a valid GeoJSON file containing a geometry column.
- The path to the cutter file is constructed as: `<data_path>/<cutter_path>/<cutter_file>`.


