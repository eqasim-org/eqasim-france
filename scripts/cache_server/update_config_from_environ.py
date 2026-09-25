import os
import sys
import yaml

if __name__ == '__main__':
    config_path = sys.argv[1]

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    environ_to_config = {"HOST": ("server", "host"),
                         "PORT": ("server", "port"),
                         "CACHE_DIR": ("cache", "directory"),
                         "CACHE_TTL": ("cache", "ttl"),
                         "CACHE_MAX_SIZE": ("cache", "max_size"),
                         "CONNECT_TIMEOUT": ("origin", "connect_timeout"),
                         "READ_TIMEOUT": ("origin", "read_timeout"),
                         "USER_AGENT": ("origin", "user_agent")}

    for env_var_name, entry in environ_to_config.items():
        section, param = entry
        if env_var_name in os.environ:
            if section not in config:
                config[section] = {}
            config[section][param] = os.environ[env_var_name]

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)