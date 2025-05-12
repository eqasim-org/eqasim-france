from synpp import ConfigurationContext, ExecuteContext

import os
import subprocess as sp
import matsim.runtime.git as git

DEFAULT_NM_BRANCH = "main"


def configure(context: ConfigurationContext):
    context.config("noisemodelling_branch", DEFAULT_NM_BRANCH)
    context.config(
        "noisemodelling_repository", "https://github.com/Symexpo/matsim-noisemodelling.git"
    )

    context.stage("matsim.runtime.git")


def run(context: ExecuteContext, arguments: list):
    # Make sure there is a dependency
    context.stage("noise.runtime.noisemodelling")

    commandline = 'gradlew run --args="%s"' % " ".join(arguments)
    
    print("Running command:\n", commandline)

    # Run the command with the specified arguments
    sp.run(commandline, cwd="%s/matsim-noisemodelling" % context.path("noise.runtime.noisemodelling"), shell=True, check=True)

def execute(context: ExecuteContext):
    # Clone repository and checkout version
    branch = context.config("noisemodelling_branch")

    git.run(
        context,
        [
            "clone",
            "--single-branch",
            "-b",
            branch,
            context.config("noisemodelling_repository"),
            "matsim-noisemodelling",
        ],
    )

    for root, dirs, files in os.walk("%s/matsim-noisemodelling" % context.path()):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o777)
        for f in files:
            os.chmod(os.path.join(root, f), 0o777)

    # run the gradle build and pipe output to stdout
    sp.run(
        ["gradlew.bat", "build", "--no-daemon", "-x", "test"],
        cwd="%s/matsim-noisemodelling" % context.path(),
        shell=True,
        check=True,
    )
