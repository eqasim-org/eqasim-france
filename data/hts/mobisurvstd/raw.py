import os

import mobisurvstd

"""
This stage standardize the input HTS to the MobiSurvStd format.
"""


def configure(context):
    context.config("data_path")
    context.config("mobisurvstd.path")

def survey_path(context):
    return os.path.join(context.config("data_path"), context.config("mobisurvstd.path"))


def execute(context):
    std_survey = mobisurvstd.standardize(
        source=survey_path(context), output_directory=None, skip_spatial=True
    )
    if std_survey is None:
        raise RuntimeError("The HTS survey could not be imported by MobiSurvStd")
    return std_survey


def validate(context):
    path = survey_path(context)
    assert os.path.isfile(path) or os.path.isdir(path), f"Cannot read HTS survey from `{path}`"
