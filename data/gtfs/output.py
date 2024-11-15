import zipfile, glob

"""
Writes out the consolidated GTFS feed
"""


def configure(context):
    context.config("output_path")
    context.config("output_prefix")

    context.stage("data.gtfs.cleaned")


def execute(context):
    source_path = "%s/output" % context.path("data.gtfs.cleaned")
    output_path = "%s/%sgtfs.zip" % (
        context.config("output_path"),
        context.config("output_prefix"),
    )

    f = zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED)
    print(source_path)

    for path in sorted(list(glob.glob("%s/*.txt" % source_path))):
        name = path.replace(source_path, "")[1:]

        if len(name) > 0:
            f.write("%s/%s" % (source_path, name), name)

    f.close()
