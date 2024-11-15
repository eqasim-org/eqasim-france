import subprocess as sp
import os, shutil


def configure(context):
    context.config("java_binary", "java")
    context.config("java_memory", "50G")


def run(
    context,
    entry_point,
    arguments=[],
    class_path=None,
    vm_arguments=[],
    cwd=None,
    memory=None,
    mode="raise",
):
    """
    This function calls java code. There are three modes:
    - return_code: Returns the return code of the Java call
    - output: Returns the output of the Java call
    - raise (default): Raises an exception if the return code is not zero
    """
    # Make sure there is a dependency
    context.stage("matsim.runtime.java")

    # Prepare temp folder
    temp_path = "%s/__java_temp" % context.path()
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)

    # Prepare arguments
    memory = context.config("java_memory") if memory is None else memory
    vm_arguments = [
        "-Xmx" + memory,
        "-Djava.io.tmpdir=%s" % temp_path,
        "-Dmatsim.useLocalDtds=true",
    ] + vm_arguments

    # Prepare classpath
    if type(class_path) == list or type(class_path) == tuple:
        class_path = ":".join(class_path)

    # Preapre CWD
    if cwd is None:
        cwd = context.path()

    # Prepare command line
    command_line = (
        [shutil.which(context.config("java_binary")), "-cp", class_path]
        + vm_arguments
        + [entry_point]
        + arguments
    )

    command_line = list(map(str, command_line))

    print("Executing java:", " ".join(command_line))

    if mode == "raise" or mode == "return_code":
        return_code = sp.check_call(command_line, cwd=cwd)

        if not return_code == 0:
            raise RuntimeError("Java return code: %d" % return_code)

        return return_code
    elif mode == "output":
        return sp.check_output(command_line, cwd=cwd)
    else:
        raise RuntimeError(
            "Mode is expected to be one of 'raise', 'return_code' or 'output'"
        )


def validate(context):
    if shutil.which(context.config("java_binary")) in ["", None]:
        raise RuntimeError(
            "Cannot find Java binary at: %s" % context.config("java_binary")
        )

    if not b"11" in sp.check_output(
        [shutil.which(context.config("java_binary")), "-version"], stderr=sp.STDOUT
    ):
        print("WARNING! A Java JDK of at least version 11 is recommended.")


def execute(context):
    pass
