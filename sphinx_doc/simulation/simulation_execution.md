# Running the simulation

The pipeline can be used to generate a full runnable [MATSim](https://matsim.org/)
scenario and run it for a couple of iterations to test it. For that, you need
to make sure that the following tools are installed on your system (you can just
try to run the pipeline, it will complain if this is not the case):

- **Java** needs to be installed, with a minimum version of Java 17. In case
you are not sure, you can download the free and open [Adoptium JDK](https://adoptium.net/fr/temurin/releases/?version=17&package=jdk).
- **Maven** `>= 3.8.8` needs to be installed to build the necessary Java packages for setting
up the scenario (such as pt2matsim) and running the simulation. Maven can be
downloaded [here](https://maven.apache.org/) if it does not already exist on
your system.
- **git** `=> 2.39.2` is used to clone the repositories containing the simulation code. In
case you clone the pipeline repository previously, you should be all set.

:::{warning} Windows users :

 The cache file paths can get very long and may break the 256 characters limit in the Microsoft Windows OS. In order to avoid any issue make sure the following regitry entry is set to **1** : `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled`
 You should also activate long paths in git : `git config --system core.longpaths true`
:::

:::{warning} Ubuntu users :

In recent versions of **Ubuntu** you may need to install the `font-config` package to avoid crashes of MATSim when writing images (`sudo apt install fontconfig`).
:::

Then, open your `config.yml` and uncomment the `matsim.output` stage in the
`run` section. If you call `python3 -m synpp` again, the pipeline will know
already which stages have been running before, so it will only run additional
stages that are needed to set up and test the simulation.

After running, you should find the MATSim scenario files in the `output`
folder:

- `ile_de_france_population.xml.gz` containing the agents and their daily plans.
- `ile_de_france_facilities.xml.gz` containing all businesses, services, etc.
- `ile_de_france_network.xml.gz` containing the road and transit network
- `ile_de_france_households.xml.gz` containing additional household information
- `ile_de_france_transit_schedule.xml.gz` and `ile_de_france_transit_vehicles.xml.gz` containing public transport data
- `ile_de_france_config.xml` containing the MATSim configuration values
- `ile_de_france_run.jar` containing a fully packaged version of the simulation code including MATSim and all other dependencies

If you want to run the simulation again (in the pipeline it is only run for
two iterations to test that everything works), you can now call the following:

```bash
java -Xmx14G -cp ile_de_france_run.jar org.eqasim.ile_de_france.RunSimulation --config-path ile_de_france_config.xml
```

This will create a `simulation_output` folder (as defined in the `ile_de_france_config.xml`)
where all simulation is written.

For more flexibility and advanced simulations, have a look at the MATSim
simulation code provided at https://github.com/eqasim-org/eqasim-java. The generated
`ile_de_france_run.jar` from this pipeline is an automatically compiled version of
this code.

## Mode choice

The population files for MATSim will automatically contain randomly assigned transport modes for the trips performed by the agents. In the mode choice process of MATSim, the modes will be adjusted and chosen according to the specific travel conditions of the agents. 

It is possible to perform an upfront mode choice based on freeflow travel times that assigns more realistic modes by performing a 100% mode choice on ideal traffic conditions. To do so, update the `mode_choice` configuration entry in the `config.yml` configuration file. Once the pipeline is run again, the modes will be present in the population:

```yaml
config:
  mode_choice: true
```

## Optionnaly export detailed link geometries

When creating the matsim network from the OSM data, the `pt2matsim` project simplifies link geometries.
You can export a `detailed_network.csv` file containing the detailed geometries of every network link by the following in the`config.yml` file :

```yaml
# ...

config:
  export_detailed_network: True

# ...
```

## Using MATSim's emissions contrib

In order to use a detailed emissions analysis, you need to let the pipeline generate a meaningful vehicle fleet. Data on the private vehicle stock across France are available from the Ministry of Ecology:

- [Vehicle stock data](https://www.statistiques.developpement-durable.gouv.fr/donnees-sur-le-parc-automobile-francais-au-1er-janvier-2021)
- Click on *Données sur les voitures particulières* (first tab) to get information on the private vehicles
- Download *Données régionales des voitures particulières - 2011 à 2021*
- Download *Données communales des voitures particulières - 2011 à 2021*
- Put both zip files into `data/vehicles`

In the `config.yml`, you must enable the vehicle fleet generation :

```yaml
config:
  vehicles_method: fleet_sample
```

After doing so, the `vehicles.xml.gz` and `vehicle_types.xml.gz` in the output will not only contain default vehicles and vehicle types, but realistic ones, based on the regional probabilities.

You can also choose to generate vehicles for a different year. The 2021 edition ZIP, for instance, contains all the years from 2012 and newer editions will contain more recent years. You can choose the year by setting:

```yaml
config:
  vehicles_year: 2015
```

Once have run a full simulation, you'll be able to use some classes defined in `eqasim-java` to analyse and compute emissions based on the MATSim outputs. For example:

```bash
java -cp ile_de_france_run.jar org.eqasim.ile_de_france.emissions.RunComputeEmissionsEvents --config-path config.xml --hbefa-cold-avg ./EFA_ColdStart_Vehcat_2015_Cold_Average.csv --hbefa-hot-avg ./EFA_HOT_Vehcat_2015_Hot_Average.csv --hbefa-cold-detailed ./EFA_ColdStart_Subsegm_2015_Cold_Detailed.csv --hbefa-hot-detailed ./EFA_HOT_Subsegm_2015_Hot_Detailed.csv
```

```bash
java -cp ile_de_france_run.jar org.eqasim.ile_de_france.emissions.RunExportEmissionsNetwork --config-path config.xml --time-bin-size 3600
```

```bash
java -cp ile_de_france_run.jar org.eqasim.ile_de_france.emissions.RunComputeEmissionsGrid --config-path config.xml --domain-shp-path idf_2154.shp
```

Please note that you need a copy of the HBEFA database in order to run those. For further information you can look at [eqasim-java](https://github.com/eqasim-org/eqasim-java) and [matsim-libs/contribs/emissions](https://github.com/matsim-org/matsim-libs/tree/master/contribs/emissions)
