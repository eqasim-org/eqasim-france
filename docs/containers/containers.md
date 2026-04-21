# Containers

You can run the eqasim pipeline as a container. This means that all dependencies will be pre-packaged and you only need to provide (1) the config file, (2) the data directory, (3) the output directory, and optionally the cache directory.

## Running

You can run the prebuilt Docker container like so:

```bash
docker run --rm -it \
    -v /path/to/local/config.yml:/eqasim/config.yml \
    -v /path/to/local/data:/eqasim-data \
    -v /path/to/local/output:/eqasim-data \
    ghcr.io/eqasim-org/eqasim-france:latest
```

Note the following requirements:
- The `data_path` in your `config.yml` must point to `/eqasim-data`.
- The `output_path` in your `config.yml` must point to `/eqasim-output`.

Furthermore, you can override the cache directroy, otherwise all cache data will be generated on the fly inside the container and deleted after execution:

```bash
-v /path/to/local/cache:/eqasim-cache
```

## Building

In case you want to build the container on your own, use the following command:

```bash
docker build -t eqasim .
```
