import shutil

"""
Writes out the consolidated GTFS feed
"""

def configure(context):
    context.config("output_path")
    context.config("output_prefix")

    context.stage("data.gtfs.cleaned")

def execute(context):
    source_path = "{}/gtfs.zip".format(context.path("data.gtfs.cleaned"))
    output_path = "{}/{}gtfs.zip".format(
        context.config("output_path"), context.config("output_prefix"))
    shutil.copyfile(source_path, output_path)
