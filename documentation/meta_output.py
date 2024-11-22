import os, datetime, json
import subprocess as sp

def configure(context):
    context.stage("matsim.runtime.git")
    context.config("output_path")
    context.config("output_prefix", "ile_de_france_")

    for option in ("sampling_rate", "hts", "random_seed"):
        context.config(option)

def get_version():
    version_path = os.path.dirname(os.path.realpath(__file__))
    version_path = os.path.realpath("{}/../version.txt".format(version_path))

    with open(version_path) as f:
        return f.read().strip()

def get_commit():
    root_path = os.path.dirname(os.path.realpath(__file__))
    root_path = os.path.realpath("{}/..".format(root_path))

    try:
        return sp.check_output(["git", "rev-parse", "HEAD"], cwd = root_path).strip().decode("utf-8")
    except sp.CalledProcessError:
        return "unknown"

def execute(context):
    # Write meta information
    information = dict(
        sampling_rate = context.config("sampling_rate"),
        hts = context.config("hts"),
        random_seed = context.config("random_seed"),
        created = datetime.datetime.now(datetime.timezone.utc).isoformat(),
        version = get_version(),
        commit = get_commit()
    )

    with open("%s/%smeta.json" % (context.config("output_path"), context.config("output_prefix")), "w+") as f:
        json.dump(information, f, indent = 4)

def validate(context):
    return get_version()
