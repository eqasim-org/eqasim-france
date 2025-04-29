# Analysing synthetic population

In addition to creating synthetic populations, it is possible to output files for analysis.

## Comparison population on grid

Using the comparison_flow_volume pipeline in the Analysis directory, you can generate grids comparing the volumes of two synthetic populations on a grid of 1km² squares for each age group and each purpose of their trips. Like with population creation, the pipeline is run with the [synpp](https://github.com/eqasim-org/synpp) runner and all parameters needed must be included in the `config.yml` file.

To be able to use this pipeline, you must already have create at least one synthetic population (1 for volume visualization and 2 for comparison) and [download France grid from INSEE](https://www.insee.fr/fr/statistiques/fichier/6214726/grille200m_gpkg.zip). From this *zip* file,  you need to extract `grille200m_metropole.gpkg` and put it into `data/grid`.

Then you need to open the `config.yml` and add the `analysis.grid.comparison_flow_volume` stage in the `run` section. To proprely use the comparison_flow_volume pipeline,you'd have to provide the following config:

```yaml
config:
  output_prefix: name_output_studied_
  comparison_file_prefix: name_output_compared_
  analysis_from_file: true
```

Before running it, make sur that populations have same format of file.
After running, you should find all grids for each age group and each trips' purpose in the `output`
folder as: `{output_prefix}_{age group}_{trip pupose}.html`

Note:
With `analysis_from_file` at False, the last synthetic population is studied by default. Also if `output_prefix` and `comparison_file_prefix` refer to the same outputs, or `comparison_file_prefix` is not specified, then only a volume visualisation of this particular population is produced.


## Compare population to source data

Using the population pipeline in the Analysis directory, you can generate multiple tables comparing composition of synthetic population to source data. Right now the tables generated compare : population volume by age range, households volume by number of vehicles, population volume with a license and without, trip volume by age range and trip volume by length.
Complementary from the synthetic population only, a table of population volume by age range and trip purpose is also created.

To be able to use this pipeline, you must already have create a synthetic population. Then you need to open the `config.yml` and add the `analysis.synthesis.population` stage in the `run` section. 