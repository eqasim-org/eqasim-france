import synpp
import os
import hashlib, gzip
from . import testdata
import sqlite3
import shutil, json

class HashManager:
    def __init__(self):
        self.valid = True
        self.information = []

    def check(self, name, path, expected):
        actual = self._hash(path)

        valid = actual == expected
        self.valid &= valid

        self.information.append({
            "name": name, "path": path,
            "expected": expected, "actual": actual,
            "valid": valid
        })

        if valid:
            print("HashManager :: ", " OK", name, expected)

        else:
            print("HashManager :: ", "NOK", name, "ac:" + actual, "!=", "ex:" + expected)

    def finish(self):
        errors = [
            dict(name = item["name"], expected = item["expected"], actual = item["actual"])
            for item in self.information if not item["valid"]
        ]

        assert self.valid, errors

    def _hash(self, path):
        if not os.path.exists(path):
            return "MISSING FILE"
        elif path.endswith(".gpkg"):
            return self._hash_db(path)
        else:
            return self._hash_file(path)

    def _hash_file(self, path):
        hash = hashlib.md5()

        # Gzip saves time stamps, so the gzipped files are NOT the same!
        opener = lambda: open(path, "rb")

        if path.endswith(".gz"):
            opener = lambda: gzip.open(path)

        with opener() as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash.update(chunk)

        f.close()

        return hash.hexdigest()

    def _hash_db(self, path):
        con = sqlite3.connect(path)

        data = []
        for line in con.iterdump():
            if not "rtree" in line: # Fix for compatibilit between Linux and Windows
                line = line.replace("MEDIUMINT", "INTEGER") # Fix for compatibilit between Linux and Windows
                data.append(line.encode())

        con.close()

        data = sorted(data)

        hash = hashlib.md5()
        for item in data:
            hash.update(item)

        return hash.hexdigest()

def test_determinism(tmpdir):
    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    for index in range(2):
        _test_determinism(index, data_path, tmpdir)

def _test_determinism(index, data_path, tmpdir):
    print("Running index %d" % index)

    cache_path = str(tmpdir.mkdir("cache_%d" % index))
    output_path = str(tmpdir.mkdir("output_%d" % index))
    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = "entd",
        random_seed = 1000, processes = 1,
        secloc_maximum_iterations = 10,
        maven_skip_tests = True,
        matching_attributes = [
            "sex", "any_cars", "age_class", "socioprofessional_class",
            "income_class", "departement_id"
        ]
    )

    stages = [
        dict(descriptor = "synthesis.output"),
    ]

    synpp.run(stages, config, working_directory = cache_path)

    manager = HashManager()

    manager.check(
        "ile_de_france_households.csv",
        "{}/ile_de_france_households.csv".format(output_path),
        "7ab3031b82d378e264f3fee5c369daa6")

    manager.check(
        "ile_de_france_persons.csv",
        "{}/ile_de_france_persons.csv".format(output_path),
        "0c49473477f527df1ddec9203b81d918")

    manager.check(
        "ile_de_france_activities.csv",
        "{}/ile_de_france_activities.csv".format(output_path),
        "8dbe756b82f6d8ff55916ad0570c5910")

    manager.check(
        "ile_de_france_trips.csv",
        "{}/ile_de_france_trips.csv".format(output_path),
        "432b6c399e964002818deeed6b5f480e")

    manager.check(
        "ile_de_france_vehicle_types.csv",
        "{}/ile_de_france_vehicle_types.csv".format(output_path),
        "e35f237b15dbd76b1fa137f01f54d1c1")

    manager.check(
        "ile_de_france_vehicles.csv",
        "{}/ile_de_france_vehicles.csv".format(output_path),
        "1151d40b07c612b62ec40ff40d3e9272")

    manager.check(
        "ile_de_france_activities.gpkg",
        "{}/ile_de_france_activities.gpkg".format(output_path),
        "a676b3708b72650e0386e6adc7415025")

    manager.check(
        "ile_de_france_commutes.gpkg",
        "{}/ile_de_france_commutes.gpkg".format(output_path),
        "4dd6e54d87da7afb6ea647d49eb384be")

    manager.check(
        "ile_de_france_homes.gpkg",
        "{}/ile_de_france_homes.gpkg".format(output_path),
        "8dc69f257ad29c6b87ba90f16bf5f9eb")

    manager.check(
        "ile_de_france_trips.gpkg",
        "{}/ile_de_france_trips.gpkg".format(output_path),
        "d47e2155195213e6cf6c5e335c3952b7")

    manager.finish()

def test_determinism_matsim(tmpdir):
    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    for index in range(2):
        _test_determinism_matsim(index, data_path, tmpdir)

def _test_determinism_matsim(index, data_path, tmpdir):
    print("Running index %d" % index)

    cache_path = str(tmpdir.mkdir("cache_%d" % index))
    output_path = str(tmpdir.mkdir("output_%d" % index))
    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = "entd",
        random_seed = 1000, processes = 1,
        secloc_maximum_iterations = 10,
        maven_skip_tests = True,
        matching_attributes = [
            "sex", "any_cars", "age_class", "socioprofessional_class",
            "income_class", "departement_id"
        ]
    )

    stages = [
        dict(descriptor = "matsim.output"),
    ]

    synpp.run(stages, config, working_directory = cache_path)

    manager = HashManager()

    manager.check(
        "ile_de_france_config.xml",
        "{}/ile_de_france_config.xml".format(output_path),
        "844c610f2e02d1bcd9b3f14b69893e75")

    manager.check(
        "ile_de_france_households.xml.gz",
        "{}/ile_de_france_households.xml.gz".format(output_path),
        "5da95bc49ec949b1c357a1531e4b5822")

    manager.check(
        "ile_de_france_vehicles.xml.gz",
        "{}/ile_de_france_vehicles.xml.gz".format(output_path),
        "be099dffb271f7e2c65459408684e213")

    manager.finish()
