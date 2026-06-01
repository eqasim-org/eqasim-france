import synpp
import os
import pandas as pd

def run_population(data_path, tmpdir, hts, update = {}):
    cache_path = str(tmpdir.mkdir("cache"))
    output_path = str(tmpdir.mkdir("output"))

    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = hts,
        random_seed = 1000, processes = 1,
        secondary_activities = dict(maximum_iterations = 10),
        maven_skip_tests = True
    )
    config.update(update)

    stages = [
        dict(descriptor = "synthesis.output"),
    ]

    synpp.run(stages, config, working_directory = cache_path)

    assert os.path.isfile("%s/ile_de_france_activities.csv" % output_path)
    assert os.path.isfile("%s/ile_de_france_persons.csv" % output_path)
    assert os.path.isfile("%s/ile_de_france_households.csv" % output_path)
    assert os.path.isfile("%s/ile_de_france_activities.gpkg" % output_path)
    assert os.path.isfile("%s/ile_de_france_trips.gpkg" % output_path)
    assert os.path.isfile("%s/ile_de_france_meta.json" % output_path)

    expected_activities = 2205
    expected_persons = 441
    expected_households = 147
    expected_vehicles = expected_persons * 2
    expected_vehicle_types = 2

    if "with_motorcycles" in update and update["with_motorcycles"] is True:
        expected_vehicles = expected_persons * 3
        expected_vehicle_types += 1 # add default motorcycle type
        if "vehicles_method" in update and update["vehicles_method"] == "fleet_sample":
            expected_vehicle_types += 47 # add all motorcycle types

    if "vehicles_method" in update and update["vehicles_method"] == "fleet_sample":
        expected_vehicle_types += 16 # add all car types

    assert expected_activities == len(pd.read_csv("%s/ile_de_france_activities.csv" % output_path, usecols = ["household_id"], sep = ";"))
    assert expected_persons == len(pd.read_csv("%s/ile_de_france_persons.csv" % output_path, usecols = ["household_id"], sep = ";"))
    assert expected_households == len(pd.read_csv("%s/ile_de_france_households.csv" % output_path, usecols = ["household_id"], sep = ";"))
    assert expected_vehicles == len(pd.read_csv("%s/ile_de_france_vehicles.csv" % output_path, usecols = ["vehicle_id"], sep = ";"))
    assert expected_vehicle_types == len(pd.read_csv("%s/ile_de_france_vehicle_types.csv" % output_path, usecols = ["type_id"], sep = ";"))

    return { "output_path": output_path }

def test_population_with_entd(data_path, tmpdir):
    run_population(data_path, tmpdir, "entd")

def test_population_with_egt(data_path, tmpdir):
    run_population(data_path, tmpdir, "egt")

def test_population_with_mode_choice(data_path, tmpdir):
    run_population(data_path, tmpdir, "entd", { "mode_choice": True })

def test_population_with_fleet_sample(data_path, tmpdir):
    run_population(data_path, tmpdir, "entd", { 
        "vehicles_method": "fleet_sample",
        "vehicles_year": 2021
    })

def test_population_with_bhepop2_income(data_path, tmpdir):
    run_population(data_path, tmpdir, "egt", { 
        "income_assignation_method": "bhepop2"
    })

def test_population_with_urban_type(data_path, tmpdir):
    run_population(data_path, tmpdir, "entd", { 
        "use_urban_type": True, 
        "matching_attributes": [
            "urban_type", "*default*"
        ],
        "matching_minimum_observations": 5
    })

def test_population_with_urban_type_and_egt(data_path, tmpdir):
    run_population(data_path, tmpdir, "egt", { 
        "use_urban_type": True, 
        "matching_attributes": [
            "urban_type", "*default*"
        ],
        "matching_minimum_observations": 5
    })

def test_population_with_motorcycles(data_path, tmpdir):
    run_population(data_path, tmpdir, "entd", {
        "with_motorcycles": True,
        "vehicles_method": "fleet_sample",
        "vehicles_year": 2021
    })

def test_population_with_secondary_activity_force_model(data_path, tmpdir):
    run_population(data_path, tmpdir, "entd", { 
        "secondary_activities": dict(chain_solver = "force_model", maximum_iterations = 10)
    })

def test_population_with_census_attributes(tmpdir):
    output_path = run_population(tmpdir, "entd", { 
        "census_attributes": [
            { "name": "household_type", "raw": "MODV", "scope": "household" },
            { "name": "rooms", "raw": "NBPI" },
        ]
    })["output_path"]

    df = pd.read_csv("%s/ile_de_france_persons.csv" % output_path, sep = ";", nrows = 2)
    assert "rooms" in df

    df = pd.read_csv("%s/ile_de_france_households.csv" % output_path, sep = ";", nrows = 2)
    assert "household_type" in df
