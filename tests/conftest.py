from . import testdata

import pytest
import tempfile
import shutil
import os

@pytest.fixture(scope = "session")
def data_path():
    directory = "{}/.pytest-eqasim-france-fixtures".format(tempfile.gettempdir())

    if os.path.exists(directory):
        print("Cleaning up existing fixture data...")
        shutil.rmtree(directory)

    os.makedirs(directory)

    print("Creating fixture data...")
    testdata.create(directory)

    print("Fixture data is ready!")
    yield directory
