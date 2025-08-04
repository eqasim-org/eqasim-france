import mobisurvstd

"""
This stage standardize the input HTS to the MobiSurvStd format.
"""


def configure(context):
    context.config("mobisurvstd.path")


def execute(context):
    std_survey = mobisurvstd.standardize(
        source=context.config("mobisurvstd.path"), output_directory=None, skip_spatial=True
    )
    return std_survey


def validate(context):
    survey_type = mobisurvstd.utils.guess_survey_type(context.config("mobisurvstd.path"))
    if survey_type is None:
        raise RuntimeError(
            "Cannot read HTS survey from: `{}`".format(context.config("mobisurvstd.path"))
        )
