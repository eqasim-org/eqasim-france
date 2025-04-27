# Containers

Containers for running the Eqasim pipeline are located in the `containers` folder

## Docker container

To build the container :
`docker build -t eqasim .`

This will pull the conda environment from the current repo.

To build using your own environment.yml file :
`docker build --build-arg env_path=/path/to/my/environment.yml -t eqasim .`

To run the pipeline : 
```bash
docker run --rm -it \
    --mount type=bind,src=/path/to/eqasim-ile-de-france,target=/usr/local/eqasim \
    --mount type=bind,src=/path/to/eqasim-data,target=/usr/local/eqasim-data \
    ghcr.io/eqasim-org/ile-de-france:latest /bin/bash -l -c "cd /usr/local/eqasim && python -m synpp"`
```

where :

- `/path/to/eqasim-ile-de-france` is the path of the [eqasim pipline](https://github.com/eqasim-org/ile-de-france) on your *host* machine.
- `/usr/local/eqasim` is going to be the path of the eqasim pipeline inside the container.
- `/path/to/eqasim-data` is the path of the data (bdtopo, hts, sirene, etc.) folder on your *host* machine.
- `/usr/local/eqasim-data` is the path of the data folder in the container. **This is the path you need to put in your `congif.yml` file**

## Apptainer 

To build the container : 
`apptainer -v -d build eqasim.sif apptainer.def`

To run the pipeline : 
`apptainer run eqasim.sif`
