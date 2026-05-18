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
        secondary_activities = dict(maximum_iterations = 10),
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
        "c530f2c5448de05951badbb350596da1")

    manager.check(
        "ile_de_france_persons.csv",
        "{}/ile_de_france_persons.csv".format(output_path),
        "534b4d6f9a4b3f4c2b2b0bc2e35c4587")

    manager.check(
        "ile_de_france_activities.csv",
        "{}/ile_de_france_activities.csv".format(output_path),
        "89b38b842359c77e1f5a51692d0cd8e3")

    manager.check(
        "ile_de_france_trips.csv",
        "{}/ile_de_france_trips.csv".format(output_path),
        "766145c0025d1cebb99dda70b535f4a6")

    manager.check(
        "ile_de_france_vehicle_types.csv",
        "{}/ile_de_france_vehicle_types.csv".format(output_path),
        "e35f237b15dbd76b1fa137f01f54d1c1")

    manager.check(
        "ile_de_france_vehicles.csv",
        "{}/ile_de_france_vehicles.csv".format(output_path),
        "4ceb5f779a32236859735219eebc45ad")

    manager.check(
        "ile_de_france_activities.gpkg",
        "{}/ile_de_france_activities.gpkg".format(output_path),
        "a3caa84f909456ef8c0e57243a343c27")

    manager.check(
        "ile_de_france_commutes.gpkg",
        "{}/ile_de_france_commutes.gpkg".format(output_path),
        "1a5e7bfbb114ede94f520f0416c715b9")

    manager.check(
        "ile_de_france_homes.gpkg",
        "{}/ile_de_france_homes.gpkg".format(output_path),
        "bb3b0ecc0796425b6c9f1d02833e146d")

    manager.check(
        "ile_de_france_trips.gpkg",
        "{}/ile_de_france_trips.gpkg".format(output_path),
        "0d9c1bf9816273c8755d9390a04792d2")

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
        secondary_activities = dict(maximum_iterations = 10),
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
        "4f3d950cedbe0a96971df577947a87dd")

    manager.check(
        "ile_de_france_vehicles.xml.gz",
        "{}/ile_de_france_vehicles.xml.gz".format(output_path),
        "63d2f2c7c8096d4f881a9a16c4e406e7")

    manager.finish()
