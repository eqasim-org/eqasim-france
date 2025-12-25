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
            print("Hash:", " OK", name, expected)

        else:
            print("Hash:", "NOK", name, "ac:" + actual, "!=", "ex:" + expected)

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
        "e1e805d7f2f5af1c058df7432318e596")
    
    manager.check(
        "ile_de_france_persons.csv",
        "{}/ile_de_france_persons.csv".format(output_path),
        "14331fd23121c64ba1494a7c1d356702")
    
    manager.check(
        "ile_de_france_activities.csv",
        "{}/ile_de_france_activities.csv".format(output_path),
        "3bf2f0cb0214f9d243936a608bd48f8b")
    
    manager.check(
        "ile_de_france_trips.csv",
        "{}/ile_de_france_trips.csv".format(output_path),
        "153a48d6df448af9b32acfe99221fe90")
    
    manager.check(
        "ile_de_france_vehicle_types.csv",
        "{}/ile_de_france_vehicle_types.csv".format(output_path),
        "af7578c363ed4e7a23163b4ab554a0e1")
    
    manager.check(
        "ile_de_france_vehicles.csv",
        "{}/ile_de_france_vehicles.csv".format(output_path),
        "1151d40b07c612b62ec40ff40d3e9272")
    
    manager.check(
        "ile_de_france_activities.gpkg",
        "{}/ile_de_france_activities.gpkg".format(output_path),
        "aa86e232f1497a25d6855d47fa5c040a")

    manager.check(
        "ile_de_france_commutes.gpkg",
        "{}/ile_de_france_commutes.gpkg".format(output_path),
        "a9b648f5083f2fbe7b304b076bc00afa")
    
    manager.check(
        "ile_de_france_homes.gpkg",
        "{}/ile_de_france_homes.gpkg".format(output_path),
        "930ce972f0f5a6f4307bc741f4cbcc80")
    
    manager.check(
        "ile_de_france_trips.gpkg",
        "{}/ile_de_france_trips.gpkg".format(output_path),
        "511693fa5d6970b43800ead2b4aa2982")

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
        "30871dfbbd2b5bf6922be1dfe20ffe73")
    
    manager.check(
        "ile_de_france_households.xml.gz",
        "{}/ile_de_france_households.xml.gz".format(output_path),
        "42fee71fe5ad5906d76c6cf87a354a3f")
    
    manager.check(
        "ile_de_france_vehicles.xml.gz",
        "{}/ile_de_france_vehicles.xml.gz".format(output_path),
        "1f3c393ea69b557798ab0915581e33a4")

    manager.finish()
