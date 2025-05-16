from synpp import ConfigurationContext, ExecuteContext
import os
import shlex
import subprocess
import platform
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

    project_dir = context.path("noise.runtime.noisemodelling") + "/matsim-noisemodelling"
    gradle_args = 'run --args="%s"' % " ".join(arguments)

    print("Running Gradle task with arguments:\n", gradle_args)

    # Use the Gradle utility to run the task
    run_gradlew_task(gradle_args, project_dir)


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

    # Use the Gradle utility to build the project
    project_dir = context.path() + "/matsim-noisemodelling"
    run_gradlew_task("build -x test", project_dir)


def run_gradlew_task(task, project_dir):
    """
    Runs a Gradle task using gradlew, supporting both Windows and Linux/macOS.

    :param task: The Gradle task to run (e.g., "build").
    :param project_dir: Path to the root of the Gradle project.
    """
    is_windows = platform.system() == "Windows"
    gradlew_script = "gradlew.bat" if is_windows else "./gradlew"

    # Optional: make gradlew executable on Unix systems
    if not is_windows:
        gradlew_path = os.path.join(project_dir, "gradlew")
        subprocess.run(["chmod", "+x", gradlew_path], check=True)

    # Split the task and options into a list
    task_args = shlex.split(task)

    subprocess.run(
        [gradlew_script] + task_args,
        cwd=project_dir,
        check=True,
        text=True,
        shell=is_windows,  # On Windows, shell=True helps with .bat files
    )
