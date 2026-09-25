import subprocess as sp
import shutil, re
from packaging.version import Version

def configure(context):
    context.config("git_binary", "git")

def run(context, arguments = [], cwd = None, catch_output = False):
    """
        This function calls git.
    """
    if cwd is None:
        cwd = context.path()

    command_line = [
        shutil.which(context.config("git_binary"))
    ] + arguments

    if catch_output:
        return sp.check_output(command_line, cwd = cwd).decode("utf-8").strip()

    else:
        return_code = sp.check_call(command_line, cwd = cwd)

        if not return_code == 0:
            raise RuntimeError("Git return code: %d" % return_code)

def validate(context):
    if shutil.which(context.config("git_binary")) in ["", None]:
        raise RuntimeError("Cannot find git binary at: %s" % context.config("git_binary"))

    version = str(sp.check_output([
        shutil.which(context.config("git_binary")),
        "--version"
    ], stderr = sp.STDOUT)).strip()

    if version.endswith("."): # fix for Windows
        version = version[:-1]

    version = re.search(r"git version ([0-9.]+)", version)

    if version:
        version = Version(version.group(1))

    if version < Version("2.0.0"):
        print(f"WARNING! Git of at least version 2.0.0 is recommended. Found: {version}")
