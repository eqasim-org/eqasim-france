import synpp
import yaml
import os
import logging
import sys


def to_absolute(p, base_path):
    if p is None:
        return p
    if not os.path.isabs(p):
        return os.path.join(base_path, p)
    return p


def to_absolute_in_dict(target_dict, key, base_path):
    if key in target_dict and target_dict[key] is not None:
        target_dict[key] = to_absolute(target_dict[key], base_path)


def build_from_yml(config_path, config_overrides):
    with open(config_path) as f:
        settings = yaml.load(f, Loader=yaml.SafeLoader)

    definitions = []

    for item in settings["run"]:
        parameters = {}

        if type(item) == dict:
            key = list(item.keys())[0]
            parameters = item[key]
            item = key

        definitions.append({
            "descriptor": item, "config": parameters
        })

    relative_config_paths = ["data_path", "output_path"]

    config_base_path = os.path.normpath(os.path.join(config_path, ".."))

    config = settings["config"] if "config" in settings else {}

    config.update(overrides)

    for key in relative_config_paths:
        to_absolute_in_dict(config, key, config_base_path)

    working_directory = settings["working_directory"] if "working_directory" in settings else None
    working_directory = to_absolute(working_directory, config_base_path)
    flowchart_path = settings["flowchart_path"] if "flowchart_path" in settings else None
    dryrun = settings["dryrun"] if "dryrun" in settings else False
    externals = settings["externals"] if "externals" in settings else {}
    aliases = settings["aliases"] if "aliases" in settings else {}

    return synpp.Synpp(config=config, working_directory=working_directory, definitions=definitions,
                       flowchart_path=flowchart_path, dryrun=dryrun, externals=externals, aliases=aliases)


if __name__ == "__main__":
    print(os.getcwd())
    logging.basicConfig(level=logging.INFO)

    config_file_path = sys.argv[1] if len(sys.argv) > 1 else "config.yml"

    overrides_starting_index = 2
    if "=" in config_file_path:
        config_file_path = "config.yml"
        overrides_starting_index = 1

    overrides = dict()
    for i in range(overrides_starting_index, len(sys.argv)):
        arg = sys.argv[i]
        key, value = arg.split("=")
        overrides[key] = value

    if not os.path.isfile(config_file_path):
        raise synpp.PipelineError("Config file does not exist: %s" % config_file_path)

    build_from_yml(config_file_path, overrides).run_pipeline()
