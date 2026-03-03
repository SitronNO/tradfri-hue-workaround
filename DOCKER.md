# Builing and running as a Docker container

## Build

To build the image, you should use `buildx` like this:

    docker buildx build -t tradfri-hue-workaround<:tagname> .


## Run

You need to create a valid configuration file. See README.md and/or
`config.ini.example`. 

Then run the following command to start the container:

    docker run --volume <path_to_configfile>:/code/config.ini --rm --name tradfri-hue-workaround tradfri-hue-workaround<:tagname>

If you want to run the container in the background, add `--detach` to the
command.

In the example below, the a filename of `docker.ini` was chosen for the
configfile, and using a tagname of `0.2`. The container will also run in the
background:

    docker run --detach --volume $PWD/docker.ini:/code/config.ini --rm --name tradfri-hue-workaround tradfri-hue-workaround:0.2

To view the logs from the container:

    docker logs -f tradfri-hue-workaround

