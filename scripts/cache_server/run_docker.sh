#!/bin/bash


set -e
uv  run update_config_from_environ.py config.yaml
cat config.yaml
uv run main.py