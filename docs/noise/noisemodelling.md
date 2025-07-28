# NoiseModelling Integration Documentation

## What is NoiseModelling?
[NoiseModelling](https://noisemodelling.readthedocs.io/en/latest/) is an open-source software suite for simulating and analyzing environmental noise in urban and peri-urban areas. It allows users to compute noise exposure and generate noise maps based on traffic and land use data, supporting both research and operational needs in environmental acoustics.

Here, we use the CLI project [matsim-noisemodelling](https://github.com/Symexpo/matsim-noisemodelling) that facilitates the calculation of noise exposure and the production of noise maps from the output of any matsim simulation.

---

## Configuration Options
NoiseModelling is configured through the `noise` subsection of the `config` section of your YAML configuration file. The following options are available:

- **`compute`**: (default: "exposure")
  - Specifies the type of noise computation to perform.
  - Options: `exposure` (for exposure analysis), `maps` (for noise map generation).
  - Example: `compute: exposure`

- **`time_bin_size`**: (default: 3600)
  - Size of the time bins for noise computation, in seconds.
  - Example: `time_bin_size: 3600` (for hourly bins)

- **`time_bin_min`**: (default: 0)
  - Start time for noise computation, in seconds from midnight.
  - Example: `time_bin_min: 0`

- **`time_bin_max`**: (default: 86400)
  - End time for noise computation, in seconds from midnight.
  - Example: `time_bin_max: 86400` (for 24 hours)

- **`refl_order`**: (default: 1)
  - Maximum order of sound reflections to consider in the simulation.
  - Example: `refl_order: 1`

- **`max_src_dist`**: (default: 750)
  - Maximum distance (in meters) for considering noise sources.
  - Example: `max_src_dist: 750`

- **`max_refl_dist`**: (default: 50)
  - Maximum distance (in meters) for considering sound reflections.
  - Example: `max_refl_dist: 50`

---

## Example Configuration
```yaml
run:
  - noise.simulation.run

config:
  noise:
    compute: exposure
    time_bin_size: 900
    time_bin_min: 0
    time_bin_max: 86400
    refl_order: 1
    max_src_dist: 200
    max_refl_dist: 25
```

---

## How It Works
- The pipeline uses these configuration options to control how NoiseModelling is run and what kind of outputs are produced.
- You can choose between exposure analysis and noise map generation, and fine-tune the simulation with time bins, reflection order, and distance parameters.
- The results can be used for environmental impact studies, urban planning, or public health analysis.

---

## Notes

- The noise simulation is run *after* a successful [ScenarioCutter](simulation\scenario_cutter.md)
- For more details on NoiseModelling itself, see the [official documentation](https://noisemodelling.readthedocs.io/en/latest/).

