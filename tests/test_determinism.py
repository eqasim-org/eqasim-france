import synpp
import os
import hashlib, gzip
from . import testdata
import sqlite3

def hash_sqlite_db(path):
    """
    Hash SQLite database file from its dump.

    As binary files of SQLite can be a different between OS (maybe due to a
    difference between the implementations of the driver) and only content
    matter, hashing the dump of the database is more relevant.
    """
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


def hash_file(file):
    hash = hashlib.md5()

    # Gzip saves time stamps, so the gzipped files are NOT the same!
    opener = lambda: open(file, "rb")

    if file.endswith(".gz"):
        opener = lambda: gzip.open(file)

    with opener() as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)

    f.close()
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

    REFERENCE_CSV_HASHES = {
        "ile_de_france_activities.csv":     "bdc44d328608622f4cf320f6483b7d70",
        "ile_de_france_households.csv":     "977a0ec2752e207e5ae89146e74657fd",
        "ile_de_france_persons.csv":        "0db38397d84d4dc51ed8531e7fef2cd8",
        "ile_de_france_trips.csv":          "ab331a1acccb69cdcdbcf443f4e323d7",
        "ile_de_france_vehicle_types.csv":  "af7578c363ed4e7a23163b4ab554a0e1",
        "ile_de_france_vehicles.csv":       "1151d40b07c612b62ec40ff40d3e9272",
    }

    REFERENCE_GPKG_HASHES = {
        "ile_de_france_activities.gpkg":    "945d95a5e31a490602967d0417fd8085",
        "ile_de_france_commutes.gpkg":      "318b0854644d0832405ae484f51bc3c6",
        "ile_de_france_homes.gpkg":         "8dc69f257ad29c6b87ba90f16bf5f9eb",
        "ile_de_france_trips.gpkg":         "3f9881af25ef5bda2ea9f67a3a715858",
    }

    generated_csv_hashes = {
        file: hash_file("%s/%s" % (output_path, file)) for file in REFERENCE_CSV_HASHES.keys()
    }

    generated_gpkg_hashes = {
        file: hash_sqlite_db("%s/%s" % (output_path, file)) for file in REFERENCE_GPKG_HASHES.keys()
    }

    print("Generated CSV hashes: ", generated_csv_hashes)
    print("Generated GPKG hashes: ", generated_gpkg_hashes)

    for file in REFERENCE_CSV_HASHES.keys():
        assert REFERENCE_CSV_HASHES[file] == generated_csv_hashes[file]

    for file in REFERENCE_GPKG_HASHES.keys():
        assert REFERENCE_GPKG_HASHES[file] == generated_gpkg_hashes[file]

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

    REFERENCE_HASHES = {
        #"ile_de_france_population.xml.gz":  "e1407f918cb92166ebf46ad769d8d085",
        #"ile_de_france_network.xml.gz":     "5f10ec295b49d2bb768451c812955794",
        "ile_de_france_households.xml.gz":  "8b1486a9a3c10c68885115042133c744",
        #"ile_de_france_facilities.xml.gz":  "5ad41afff9ae5c470082510b943e6778",
        "ile_de_france_config.xml":         "30871dfbbd2b5bf6922be1dfe20ffe73",
        "ile_de_france_vehicles.xml.gz":    "1f3c393ea69b557798ab0915581e33a4"
    }

    # activities.gpkg, trips.gpkg, meta.json,
    # ile_de_france_transit_schedule.xml.gz, ile_de_france_transit_vehicles.xml.gz

    # TODO: Output of the Java part is not deterministic, probably because of
    # the ordering of persons / facilities. Fix that! Same is true for GPKG. A
    # detailed inspection of meta.json would make sense!

    generated_hashes = {
        file: hash_file("%s/%s" % (output_path, file)) for file in REFERENCE_HASHES.keys()
    }

    print("Generated hashes: ", generated_hashes)

    for file in REFERENCE_HASHES.keys():
        assert REFERENCE_HASHES[file] == generated_hashes[file]
