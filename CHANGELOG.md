# Changelog

**Under development**

- feat: add population analysis output
- fix: avoid regenerating OSM when population changes
- feat: add municipality information to households and activities
- chore: update to `eqasim-java` commit `ece4932`
- feat: vehicles and vehicle types are now always generated
- feat: read vehicles data from zip files
- feat : option parameter to remove filtering for requesting departements in hts
- fix: secondary location model used same random seed in every parallel thread
- feat: add a new method for attributing income to housholds using the bhepop2 package
- fix: fixed special case in repairing ENTD for completely overlapping trips
- feat: make it possible to disable the test run of MATSim before writing everything out
- feat: check availability of open data sources for every PR
- feat: make statistical matching attribute list configurable
- feat: add urban type classifiation (unité urbaine)
- feat: functionality to make use of INSEE population projection data
- update: don't remove households with people not living/studying in Île-de-France anymore to be more consistent with other use cases
- fix bug where always one household_id existed twice
- Fix read order when exploring files using `glob`
- Modes are only written now to `trips.csv` if `mode_choice` is activated
- Update to `eqasim-java` commit `7cbe85b`
- Adding optional `eqasim-java`-based mode choice step using the `mode_choice` configuration option
- Make use of building information (housing) and addresses that are attached to them for home locatio assignment
- Make use of National Address Database (BAN)
- Further simplify handling of BD-TOPO by avoiding matching of very specific file names
- Fix: Segfault in statistical matching caused by `numba` in recent versions
- Increase reproducibility for BD-TOPO by requiring user to dump the IGN files in 7z'ed GPKG format into one central folder for `bdtopo22`
- Fix: Correctly treat non-movers in CEREMA EDGT for Lyon
- Fix: Properly treat non-movers in EDGT Lyon ADISP data
- Configure directory for GTFS and then auto-detect contained zip files
- Added integration tests for Windows
- Updated conda environment based entirely on *conda-forge*
- Use national census data to ease creation of scenarios other than IDF
- Make various inputs with long source names folder-based (OSM, BD-TOPO, IRIS, ...)
- Read input data directly from ZIP archives instead of requiring the user to unpack the files
- Update documentation for non-IDF use cases to updated data sets
- Update: Make use of INSEE RP 2019, BPE 2021, Filosofi 2019, IRIS 2021
- Make use of BD-TOPO building database for home locations
- Remove BD-TOPO address database
- Make use of georeferenced SIRENE provided by INSEE
- Update documentation for the required versions of Java and Maven
- Updated Github workflow with more reuse of existing actions
- Update synpp to `1.5.1`
- Fix: Handle commas in coordinates in BPE
- Fix: Make types consistent for mode recognition in ENTD
- Fix: Properly treat non-movers in EDGT 44
- Fix: Avoid duplicate persons in same households
- Add option to export detailed link geometries
- Fix: Arbitrary order of week days in merged GTFS
- Use BPE 2021 instead of BPE 2019
- Update configuration files for Lyon, Nantes, Corsica
- Add a basic sample based vehicle fleet generation tailored for use with the `emissions` matsim contrib
- Fixing socioprofessional category for Nantes and Lyon (Cerema)
- Fix documentation and processing for Nantes GTFS
- Add law status of the SIRENE enterprises for down-stream freight models (this requires both SIREN and SIRET data as input!)
- Update handling of invalid values on the nubmer of employees in SIRENE
- Add alternative source for EDGT Lyon (and set it as default/recommended source)
- Add euclidean distance to Nantes/Lyon GTFS output
- Fix GTFS schedules without transfer times
- Added stage to write out the full merged GTFS feed: `data.gtfs.output`
- Bugfix: Sometimes bug in converting GTFS coordinates (esp. Lyon / Nantes)
- Fixing output stages
- Add output stages for SIRENE and the selected HTS
- Add output prefix to non-MATSim output files as well
- Add code and documentation for Nantes use case
- Bugfix: Generate `meta.json` when code was not cloned but downloaded directly
- Use `eqasim-java:1.3.1`
- Make choice of branch and version of pt2matsim more flexible
- Improve handling of Osmosis on Windows
- Add stages to process EDGT for Lyon

**1.2.0**

- Update code and data to BPE 2019 (verison for 2018 is not available anymore)
- Add additional spatial standard output: `homes.gpkg` and `commutes.gpkg`
- Updated documentation for BD-TOPO
- By default, load SIRENE directly from `zip` file instead of `csv`
- Bugfix: Make sure df_trips are sorted properly in `synthesis.population.trips`
- Bugfix: Do not execute "urban" attribute imputation twice
- Bugfix: Do not consider *inactive* enterprises from SIRENE
- Update analysis scripts
- Remove CRS warnings
- Bugfix: Handle case if very last activity chain in population ends with tail
- Speed up and improve testing
- Improve analysis output for ENTD
- Update to `eqasim-java:1.2.0` to support tails and "free" activity chains
- Allow for activity chains that do not start and end at home
- Improve handling of education attribute in ENTD

**1.1.0**

- Update to `synpp:1.3.1`
- Use addresses for home locations (from BD-TOPO)
- Use enterprise addresses for work locations (from SIRENE + BD-TOPO)
- Add SIRENE and BD-TOPO data sets
- Update to `eqasim-java:1.1.0` and MATSim 12
- Preparation to use Corisca scenario (see config_corsica.yml) as unit test input in `eqasim-java`
- Several auto-fixes for malformatted GTFS schedules (mainly Corsica)
- Make jar output optional and use proper prefix
- Bugfix: Fixing bug where stop times where discarded in GTFS cutting
- Add documentation for Lyon and Toulouse
- Define stage to output HTS reference data
- Make prefix of MATSim output files configurable
- Cut GTFS schedules to the scenario area automatically
- Make possible to merge multiple GTFS files automatically
- Automatically convert, filter and merge OSM data before using it in pt2matsim. This requires that `osmosis` is available in the run environment.
- Provide calibrated Île-de-France/Paris eqasim simulation for 5% sample
- Make use of `isUrban` attribute from eqasim `1.0.6`
- Update to eqasim `1.0.6`
- Make GTFS date configurable
- Use synpp 1.2.2 to fix Windows directory regeneration issue
- Make pipeline configurable for other departments and regions, add documentation
- BC: Make use of INSEE zone summary data (`codes_2017`)
- Add configuration parameters to filter for departments and regions
- Fixed destinations that have coordinates outside of their municipality
- Make error message for runtime dependencies more verbose
- Switch default instructions to Anaconda

**1.0.0**

- Fixed dependency issue for ENTD scenario
- Initial public version of the pipeline
