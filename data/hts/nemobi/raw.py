import os

import nemobi

"""
This stage standardize the input HTS to the Nemobi format.
"""


def configure(context):
    context.config("data_path")
    context.config("nemobi.path", None)
    context.config("mobisurvstd.path", None)  # legacy alias for nemobi.path


def survey_path(context):
    # Read path from `nemobi.path`, or `mobisurvstd.path` if the former is not defined.
    path = context.config("nemobi.path") or context.config("mobisurvstd.path")
    if path is None:
        raise RuntimeError(
            "Config option 'nemobi.path' (or 'mobisurvstd.path') is required "
            "when hts is nemobi/mobisurvstd`"
        )
    return os.path.join(context.config("data_path"), path)


def execute(context):
    std_survey = nemobi.standardize(
        source=survey_path(context), output_directory=None, skip_spatial=True
    )
    if std_survey is None:
        raise RuntimeError("The HTS survey could not be imported by Nemobi")
    return std_survey


def validate(context):
    path = survey_path(context)
    assert os.path.isfile(path) or os.path.isdir(path), f"Cannot read HTS survey from `{path}`"
