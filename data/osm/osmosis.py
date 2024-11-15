import subprocess as sp
import shutil, os


def configure(context):
    context.config("osmosis_binary", "osmosis")

    context.config("java_binary", "java")
    context.config("java_memory", "50G")


def run(context, arguments=[], cwd=None):
    """
    This function calls osmosis.
    """
    # Make sure there is a dependency
    context.stage("data.osm.osmosis")

    if cwd is None:
        cwd = context.path()

    # Prepare command line
    command_line = [shutil.which(context.config("osmosis_binary"))] + arguments

    # Prepare environment
    environment = os.environ.copy()
    environment["JAVACMD"] = shutil.which(context.config("java_binary"))
    environment["JAVACMD_OPTIONS"] = "-Xmx%s" % context.config("java_memory")

    # Run Osmosis
    return_code = sp.check_call(command_line, cwd=cwd, env=environment)

    if not return_code == 0:
        raise RuntimeError("Osmosis return code: %d" % return_code)


def validate(context):
    if shutil.which(context.config("osmosis_binary")) in ["", None]:
        raise RuntimeError(
            "Cannot find Osmosis binary at: %s" % context.config("osmosis_binary")
        )

    if not b"0.48." in sp.check_output(
        [shutil.which(context.config("osmosis_binary")), "-v"], stderr=sp.STDOUT
    ):
        print("WARNING! Osmosis of at least version 0.48.x is recommended!")


def execute(context):
    pass
