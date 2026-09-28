import yaml
import typer
from typing import Annotated
from pathlib import Path

def update(source: dict, destination: dict):
    for key, value in source.items():
        if key not in destination:
            destination[key] = value
        if key in destination:
            if isinstance(value, dict) != isinstance(destination[key], dict):
                raise Exception("%s is a dictionary in one side but not in the other" % key)
            if isinstance(value, dict):
                update(value, destination[key])
            else:
                destination[key] = value

def main(source: Annotated[Path, typer.Argument()],
         destination: Annotated[Path, typer.Argument()]):
    with open(source) as f:
        source_config = yaml.load(f, Loader=yaml.SafeLoader)
    with open(destination) as f:
        destination_config = yaml.load(f, Loader=yaml.SafeLoader)

    update(source_config, destination_config)
    with open(destination, "w") as f:
        yaml.dump(destination_config, f, Dumper=yaml.SafeDumper)


if __name__ == '__main__':
    typer.run(main)