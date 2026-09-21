import synpp
import os
import hashlib, gzip
import sqlite3

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

def test_determinism(data_path, tmpdir):
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
        "5d458e8563fb1857beee18a4e0fdae4e")

    manager.check(
        "ile_de_france_persons.csv",
        "{}/ile_de_france_persons.csv".format(output_path),
        "0ee1f26c83bcb768f8f88f2017b6ac47")

    manager.check(
        "ile_de_france_activities.csv",
        "{}/ile_de_france_activities.csv".format(output_path),
        "7bb6fa6cb6b65977270ee01d84bcd3f6")

    manager.check(
        "ile_de_france_trips.csv",
        "{}/ile_de_france_trips.csv".format(output_path),
        "7fe9d17edb680117490e9dbda058c457")

    manager.check(
        "ile_de_france_vehicle_types.csv",
        "{}/ile_de_france_vehicle_types.csv".format(output_path),
        "e35f237b15dbd76b1fa137f01f54d1c1")

    manager.check(
        "ile_de_france_vehicles.csv",
        "{}/ile_de_france_vehicles.csv".format(output_path),
        "4da2a3031482cfd730c9a87cbf173187")

    manager.check(
        "ile_de_france_activities.gpkg",
        "{}/ile_de_france_activities.gpkg".format(output_path),
        "a3b57243f566b3ec076811c6cd6c6caa")

    manager.check(
        "ile_de_france_commutes.gpkg",
        "{}/ile_de_france_commutes.gpkg".format(output_path),
        "8f5d76e2191a31683f91df625b3897ce")

    manager.check(
        "ile_de_france_homes.gpkg",
        "{}/ile_de_france_homes.gpkg".format(output_path),
        "2731ab009cf64e9b31aff66a80dac0e8")

    manager.check(
        "ile_de_france_trips.gpkg",
        "{}/ile_de_france_trips.gpkg".format(output_path),
        "c81947c1a299af93e241025544f83516")

    manager.finish()

def test_determinism_matsim(data_path, tmpdir):
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
        "a68ba0d1265c3c687023147b92a47375")

    manager.check(
        "ile_de_france_households.xml.gz",
        "{}/ile_de_france_households.xml.gz".format(output_path),
        "7778c76278eed41ec1f5be7ad0a8e5b8")

    manager.check(
        "ile_de_france_vehicles.xml.gz",
        "{}/ile_de_france_vehicles.xml.gz".format(output_path),
        "40db0b3031349b97028ff62832bd96f9")

    manager.finish()