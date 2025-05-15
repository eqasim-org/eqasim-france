import synpp
import os
from . import testdata

TEST_NOISE = True

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
        secloc_maximum_iterations = 10,
        maven_skip_tests = True,
        cutter_after_full_simulation=False,
        export_detailed_network=True,
        git_binary="C:\\Users\\lebescond\\Desktop\\_FORMATION_EQASIM\\_tools\\PortableGit\\bin\\git.exe",
        java_binary="C:\\Users\\lebescond\\Desktop\\_FORMATION_EQASIM\\_tools\\jdk-17.0.14+7\\bin\\java.exe",
        maven_binary="C:\\Users\\lebescond\\Desktop\\_FORMATION_EQASIM\\_tools\\apache-maven-3.9.9\\bin\\mvn.cmd"
    )

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
    
    config.update(dict(
        noise_time_bin_size=3600,
        noise_time_bin_min=8*3600,
        noise_time_bin_max=10*3600,
        noise_refl_order=0,
        noise_max_src_dist=50,
        noise_max_refl_dist=10,
    ))
    stages = [
        dict(descriptor = "noise.simulation.run"),
    ]
    synpp.run(stages, config, working_directory = cache_path)
