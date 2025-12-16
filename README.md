# Trådfri Hue Workaround
Workaround Script for fixing brightness issue with IKEA Trådfri lights on
Philips Hue Bridge. It works by continuously polling the Hue Bridge to detect
change in brightness, then resend the brightness command to the Trådfri light
after a short period.

## Why this project? There's a compatibility issue with IKEA Trådfri lights and
Philips Hue Bridge where the brightness is not set correctly when changing
scenes. The Hue Bridge will first send a command for color change, then
brightness. The Trådfri light will not accept any commands while it is busy
changing the color and discards the command to change its brightness. This
results in a mismatch where the Hue Bridge thinks the brightness has changed,
while it has actually not changed. 

## Requirements You'll need a PC or server where the script can run in the
background. 

It's recommended to use a Python3 virtual environment to install the required
module for this script:

1. `python3 -m venv venv`
2. `. venv/bin/activate`
3. `python3 -m pip install --upgrade -r requirements.txt`

Afterwards, if you need to active the environment again, just run:

    . venv/bin/activate

## Authentication against Philips Hue Bridge

The first time you run the script, you must press the **Link Button** on the
Philips Hue Bridge. This authenticates your client and generates a unique
username (API Key).

By default, the `phue` library saves this key in a file located at
`$HOME/.python_hue`.

### Using the Key in Config Files If you wish to use the configuration file (see
below) to define your connection settings, you should first run the script once
to generate the key. Then, you can retrieve it by reading the file:

    cat ~/.python_hue

Copy the "username" part of the JSON output and paste it into your `config.ini`
file.

## Usage

You can run the script using command-line arguments, a configuration file, or a
combination of both.

### Order of Precedence
The script determines values in the following order:
1. Command Line Arguments (e.g., `-t 0.5`)
2. Configuration File (specified via `-c` or `CONFIGFILE` env var)
3. Default Values

### 1. Command Line Simply start the script with Hue Bridge IP and Trådfri light
ID's as arguments:

    ./tradfri_hue_workaround.py <bridge_ip> <light_id_1> <light_id_2> ...

List available lights and IDs:

    ./tradfri_hue_workaround.py <bridge_ip> -l

### 2. Configuration File You can avoid typing arguments every time by using a
configuration file (INI format).

1. Copy the example config:
    ```
    cp config.ini.example config.ini`
    ```

2. Edit `config.ini` with your Bridge IP, API Key (Username), and Light IDs.

3. Run the script:
    ```
    ./tradfri_hue_workaround.py -c config.ini

    ```

You can also set the CONFIGFILE environment variable to point to your config
file, allowing you to run the script without any arguments:

    export CONFIGFILE=./config.ini ./tradfri_hue_workaround.py


### 3. Mixed usage You can override configuration file settings with
command-line arguments. For example, to use your saved config but temporarily
increase verbosity and change the poll time:

    ./tradfri_hue_workaround.py -c config.ini -vv -t 1.0


## Options

| Argument                   | Description |
| :---                       | :--- |
| `bridge_ip`                | IP address of the Hue Bridge (Optional if in config) |
| `light_ids`                | Space-separated list of Light IDs to monitor (Optional if in config) |
| `-c`, `--configfile`       | Path to configuration file |
| `-u`, `--username`         | Hue Bridge API Key/Username |
| `-l`, `--list`             | List available lights on the bridge |
| `-t`, `--poll_time`        | How often lights are checked (seconds) |
| `-d`, `--brightness_delay` | Wait time after change before updating (seconds) |
| `--max-retries`            | Maximum connection retries before exiting |
| `--retry-delay`            | Delay in seconds between retries |
| `-v`, `-vv`                | Increase logging verbosity (Info / Debug) |
