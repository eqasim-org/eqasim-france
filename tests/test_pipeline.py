import synpp
import os
import hashlib
from . import testdata
import pandas as pd

def test_data(tmpdir):
    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    cache_path = str(tmpdir.mkdir("cache"))
    output_path = str(tmpdir.mkdir("output"))
    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], hts = "entd")

    stages = [
        dict(descriptor = "data.spatial.iris"),
        dict(descriptor = "data.spatial.codes"),
        dict(descriptor = "data.spatial.population"),
        dict(descriptor = "data.bpe.cleaned"),
        dict(descriptor = "data.income.municipality"),
        dict(descriptor = "data.hts.entd.cleaned"),
        dict(descriptor = "data.hts.egt.cleaned"),
        dict(descriptor = "data.census.cleaned"),
        dict(descriptor = "data.od.cleaned"),
        dict(descriptor = "data.hts.output"),
        dict(descriptor = "data.sirene.output"),
    ]

    synpp.run(stages, config, working_directory = cache_path)

    assert os.path.isfile("%s/ile_de_france_hts_households.csv" % output_path)
    assert os.path.isfile("%s/ile_de_france_hts_persons.csv" % output_path)
    assert os.path.isfile("%s/ile_de_france_hts_trips.csv" % output_path)
    assert os.path.isfile("%s/ile_de_france_sirene.gpkg" % output_path)

def run_population(tmpdir, hts, update = {}):
    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    cache_path = str(tmpdir.mkdir("cache"))
    output_path = str(tmpdir.mkdir("output"))
    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = hts,
        random_seed = 1000, processes = 1,
        secloc_maximum_iterations = 10,
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

    assert 2235 == len(pd.read_csv("%s/ile_de_france_activities.csv" % output_path, usecols = ["household_id"], sep = ";"))
    assert 447 == len(pd.read_csv("%s/ile_de_france_persons.csv" % output_path, usecols = ["household_id"], sep = ";"))
    assert 149 == len(pd.read_csv("%s/ile_de_france_households.csv" % output_path, usecols = ["household_id"], sep = ";"))
    
    assert 447 * 2 == len(pd.read_csv("%s/ile_de_france_vehicles.csv" % output_path, usecols = ["vehicle_id"], sep = ";"))
    if "vehicles_method" in update and update["vehicles_method"] == "fleet_sample":
        assert 17 + 1 == len(pd.read_csv("%s/ile_de_france_vehicle_types.csv" % output_path, usecols = ["type_id"], sep = ";"))
    else:
        assert 2 == len(pd.read_csv("%s/ile_de_france_vehicle_types.csv" % output_path, usecols = ["type_id"], sep = ";"))

def test_population_with_entd(tmpdir):
    run_population(tmpdir, "entd")

def test_population_with_egt(tmpdir):
    run_population(tmpdir, "egt")

def test_population_with_mode_choice(tmpdir):
    run_population(tmpdir, "entd", { "mode_choice": True })

def test_population_with_fleet_sample(tmpdir):
    run_population(tmpdir, "entd", { 
        "vehicles_method": "fleet_sample",
        "vehicles_year": 2021
    })

def test_population_with_bhepop2_income(tmpdir):
    run_population(tmpdir, "egt", { 
        "income_assignation_method": "bhepop2"
    })

def test_population_with_urban_type(tmpdir):
    run_population(tmpdir, "entd", { 
        "use_urban_type": True, 
        "matching_attributes": [
            "urban_type", "*default*"
        ],
        "matching_minimum_observations": 5
    })

def test_population_with_urban_type_and_egt(tmpdir):
    run_population(tmpdir, "egt", { 
        "use_urban_type": True, 
        "matching_attributes": [
            "urban_type", "*default*"
        ],
        "matching_minimum_observations": 5
    })
