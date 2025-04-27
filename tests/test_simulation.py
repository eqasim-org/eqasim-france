import synpp
import os
import hashlib
from . import testdata

def test_simulation(tmpdir):
    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    cache_path = str(tmpdir.mkdir("cache"))
    output_path = str(tmpdir.mkdir("output"))

    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = "entd",
        random_seed = 1000, processes = 1,
        secloc_maximum_iterations = 10,
        maven_skip_tests = True
    )

    stages = [
        dict(descriptor = "matsim.output")
    ]

    synpp.run(stages, config, working_directory = cache_path)

    assert os.path.isfile("%s/ile_de_france_population.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_network.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_transit_schedule.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_transit_vehicles.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_households.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_facilities.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_vehicles.xml.gz" % output_path)
