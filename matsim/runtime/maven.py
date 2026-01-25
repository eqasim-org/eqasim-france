import subprocess as sp
import os, shutil

import matsim.runtime.java as java

def configure(context):
    java.configure(context)

    context.config("maven_binary", "mvn")
    context.config("maven_skip_tests", False)
    context.config("maven_local_cache", False)

def run(context, arguments = [], cwd = None):
    """
        This function calls Maven.
    """
    if cwd is None:
        cwd = context.path()

    # Prepare temp folder
    temp_path = "%s/__java_temp" % context.path()
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)

    vm_arguments = [
        "-Djava.io.tmpdir=%s" % temp_path
    ]

    # Prepare cache folder (optional)
    use_local_cache = context.config("maven_local_cache")
    if use_local_cache:
        cache_path = "%s/__maven_cache" % context.path()
        if not os.path.exists(cache_path):
            os.mkdir(cache_path)

        vm_arguments.append("-Dmaven.repo.local={}".format(cache_path))

    if context.config("maven_skip_tests"):
        vm_arguments.append("-DskipTests=true")

    command_line = [
        shutil.which(context.config("maven_binary"))
    ] + vm_arguments + arguments

    return_code = sp.check_call(command_line, cwd = cwd)

    if not return_code == 0:
        raise RuntimeError("Maven return code: %d" % return_code)

def validate(context):
    java.validate(context)
    
    if shutil.which(context.config("maven_binary")) in ["", None]:
        raise RuntimeError("Cannot find Maven binary at: %s" % context.config("maven_binary"))

    if not b"3." in sp.check_output([
        shutil.which(context.config("maven_binary")),
        "-version"
    ], stderr = sp.STDOUT):
        print("WARNING! Maven of at least version 3.x.x is recommended!")
