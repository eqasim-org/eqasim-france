# Scenario Cutter

The Scenario Cutter allows you to define and use a specific region of interest, such as a city or metropolitan area area for further detailed simulation or analysis. This is by providing a custom boundary (cutter) file.

The code is called from the [eqasim-java](https://github.com/eqasim-org/eqasim-java) project, here: [RunScenariojava](https://github.com/eqasim-org/eqasim-java/blob/develop/core/src/main/java/org/eqasim/core/scenario/cutter/RunScenariojava). 

## Configuration Options

The cutter is configured through the `cutter` subsection of the `config` section of your YAML configuration file. The following options are available:

- **`path`**: (default: `cutter`)
  - The relative path (from your `data_path`) to the directory containing the cutter file.
  - Example: `cutter_path: cutter`

- **`file`**: (default: `cutter.geojson`)
  - The name of the file (usually a GeoJSON) that defines the area to be used as a 
  - Example: `cutter_file: cutter.geojson`

- **`name`**: (optional)
  - A label for the cutter area, used for output file naming and documentation.
  - Example: `cutter_name: paris`

- **`after_full_simulation`**: (optional, default: `False`)
  - If set to `True`, the cutter will be applied after the full simulation is run, rather than before.
  - Example: `after_full_simulation: True`

### Example Configuration

```yaml

run:
  - matsim.simulation.cut
  # - matsim.simulation.full_run

config:
  data_path: /path/to/my/data

  cutter:
    path: cutter
    file: cutter.geojson
    name: paris
    after_full_simulation: False
```

## How It Works

- The cutter module loads the specified GeoJSON file from the directory defined by `data_path` and `cutter.path`.
- The geometry in this file is used to select or mask the area of interest for the simulation.
- If `cutter.after_full_simulation` is enabled, the full simulation is run first, and then the results are filtered to the cutter area.

## Requirements
- The cutter file must be a valid GeoJSON file containing a geometry column.
- The path to the cutter file is constructed as: `<data_path>/<cutter.path>/<cutter.file>`.


