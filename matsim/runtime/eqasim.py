import subprocess as sp
import os, os.path, shutil

import matsim.runtime.git as git
import matsim.runtime.java as java
import matsim.runtime.maven as maven

DEFAULT_EQASIM_VERSION = "1.5.0"
DEFAULT_EQASIM_BRANCH = "feat/model-2024"
DEFAULT_EQASIM_COMMIT = "25d656b"

def configure(context):
    context.stage("matsim.runtime.git")
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.maven")

    context.config("eqasim_version", DEFAULT_EQASIM_VERSION)
    context.config("eqasim_branch", DEFAULT_EQASIM_BRANCH)
    context.config("eqasim_commit", DEFAULT_EQASIM_COMMIT)
    context.config("eqasim_repository", "https://github.com/eqasim-org/eqasim-java.git")
    context.config("eqasim_path", "")

def run(context, command, arguments):
    version = context.config("eqasim_version")

    # Make sure there is a dependency
    context.stage("matsim.runtime.eqasim")

    jar_path = "%s/eqasim-java/ile_de_france/target/ile_de_france-%s.jar" % (
        context.path("matsim.runtime.eqasim"), version
    )
    java.run(context, command, arguments, jar_path)

def execute(context):
    version = context.config("eqasim_version")

    # Normal case: we clone eqasim
    if context.config("eqasim_path") == "":
        # Clone repository and checkout version
        branch = context.config("eqasim_branch")

        git.run(context, [
            "clone", "--single-branch", "-b", branch,
            context.config("eqasim_repository"), "eqasim-java"
        ])

        # Select the configured commit or tag
        commit = context.config("eqasim_commit")

        git.run(context, [
            "checkout", commit
        ], cwd = "{}/eqasim-java".format(context.path()))

        # Build eqasim
        maven.run(context, ["-Pstandalone", "--projects", "ile_de_france", "--also-make", "package", "-DskipTests=true"], cwd = "%s/eqasim-java" % context.path())

        if not os.path.exists("{}/eqasim-java/ile_de_france/target/ile_de_france-{}.jar".format(context.path(), version)):
            raise RuntimeError("The JAR was not created correctly. Wrong eqasim_version specified?")

    # Special case: We provide the jar directly. This is mainly used for
    # creating input to unit tests of the eqasim-java package.
    else:
        os.makedirs("%s/eqasim-java/ile_de_france/target" % context.path())
        shutil.copy(context.config("eqasim_path"),
            "%s/eqasim-java/ile_de_france/target/ile_de_france-%s.jar" % (context.path(), version))

    return "eqasim-java/ile_de_france/target/ile_de_france-%s.jar" % version

def validate(context):
    path = context.config("eqasim_path")

    if path == "":
        return True

    if not os.path.exists(path):
        raise RuntimeError("Cannot find eqasim at: %s" % path)
    
    if context.config("eqasim_tag") is None:
        if context.config("eqasim_commit") is None:
            raise RuntimeError("Either eqasim commit or tag must be defined")
        
    if (context.config("eqasim_tag") is None) == (context.config("eqasim_commit") is None):
        raise RuntimeError("Eqasim commit and tag must not be defined at the same time")

    return os.path.getmtime(path)
