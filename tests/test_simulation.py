import synpp
import os
from . import testdata

TEST_NOISE = False

def test_simulation(tmpdir):

    test_noise = TEST_NOISE
    if os.environ.get("TEST_NOISE") is not None:
        test_noise = os.environ.get("TEST_NOISE").lower() == "true"

    data_path = str(tmpdir.mkdir("data"))
    testdata.create(data_path)

    cache_path = str(tmpdir.mkdir("cache"))
    output_path = str(tmpdir.mkdir("output"))

    config = dict(
        data_path = data_path, output_path = output_path,
        regions = [10, 11], sampling_rate = 1.0, hts = "entd",
        random_seed = 1000, processes = 1,
        secondary_activities = dict(maximum_iterations = 10),
        maven_skip_tests = True,
        export_detailed_network=True
    )

    config.update({
        "cutter.after_full_simulation": False,
    })

    stages = [
        dict(descriptor = "matsim.output"),
        dict(descriptor = "matsim.simulation.cutter.cut"),
    ]

    synpp.run(stages, config, working_directory = cache_path)

    assert os.path.isfile("%s/ile_de_france_population.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_network.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_transit_schedule.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_transit_vehicles.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_households.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_facilities.xml.gz" % output_path)
    assert os.path.isfile("%s/ile_de_france_vehicles.xml.gz" % output_path)

    assert os.path.isfile("%s/cutter/cutter_population.xml.gz" % output_path)
    assert os.path.isfile("%s/cutter/cutter_network.xml.gz" % output_path)
    assert os.path.isfile("%s/cutter/cutter_transit_schedule.xml.gz" % output_path)
    assert os.path.isfile("%s/cutter/cutter_transit_vehicles.xml.gz" % output_path)
    assert os.path.isfile("%s/cutter/cutter_households.xml.gz" % output_path)
    assert os.path.isfile("%s/cutter/cutter_facilities.xml.gz" % output_path)
    assert os.path.isfile("%s/cutter/cutter_vehicles.xml.gz" % output_path)

    if not test_noise:
        return
    
    config.update({
        "noise.time_bin_size": 3600,
        "noise.time_bin_min": 8*3600,
        "noise.time_bin_max": 10*3600,
        "noise.refl_order": 0,
        "noise.max_src_dist": 50,
        "noise.max_refl_dist": 10,
    })
    stages = [
        dict(descriptor = "noise.simulation.run"),
    ]
    synpp.run(stages, config, working_directory = cache_path)
