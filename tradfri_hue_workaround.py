#!/usr/bin/env python3

import argparse
import logging
import socket
import configparser
import os
import sys
from phue import Bridge, PhueRequestTimeout
from time import sleep, time

# Default values (Hardcoded fallbacks)
DEFAULTS = {
    'poll_time': 0.2,
    'brightness_delay': 1.2,
    'max_retries': 5,
    'retry_delay': 5,
    'verbose': 1,
    'light_ids': [],
    'bridge_ip': None,
    'username': None
}

class TradfriLight():
    def __init__(self, light, brightness_delay = 1.0):
        self._light = light
        self._last_brightness = light.brightness
        self._brightness_delay = brightness_delay
        self._has_changed = False
        self._t0 = time()

    def check_and_update(self):
        # Retrieve brightness (this might throw an error if light is unreachable, handled in main)
        brightness = self._light.brightness
        if self._last_brightness != brightness:
            logging.info(f'Brightness changed detected for light "{self._light.name}": {self._last_brightness} -> {brightness}')
            self._has_changed = True
            self._t0 = time()

        if self._has_changed and self._t0 + self._brightness_delay < time():
            logging.info(f'Brightness for light "{self._light.name}" set to {brightness}')
            self._light.brightness = brightness
            self._has_changed = False

        self._last_brightness = brightness


def main(bridge, args):
    tradfri_ids = args.light_ids
    light_list = bridge.get_light_objects()
    # Filter lights. Handle float/int mismatch by converting to int for comparison if needed,
    # but here we rely on the input types matching the API types.
    tradfri_lights = [TradfriLight(l, brightness_delay=args.brightness_delay) for l in light_list if l.light_id in tradfri_ids]

    if not tradfri_lights:
        logging.warning("No lights found matching the provided IDs.")
        return

    logging.info(f"Monitoring {len(tradfri_lights)} lights...")

    retries = 0
    while True:
        try:
            for light in tradfri_lights:
                logging.debug(f'Checking light {light._light.name}')
                light.check_and_update()
            
            # Reset retries count after a successful run
            if retries > 0:
                logging.info("Connection re-established.")
                retries = 0

            logging.debug(f'Sleeping for {args.poll_time} seconds...')
            sleep(args.poll_time)

        except (socket.timeout, OSError, PhueRequestTimeout) as e:
            retries += 1
            logging.warning(f"Network error ({type(e).__name__}). Retrying in {args.retry_delay}s... (Attempt {retries}/{args.max_retries})")
            if retries >= args.max_retries:
                logging.error("Maximum number of retries reached. Terminating.")
                break
            sleep(args.retry_delay)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            # Optional: break or continue depending on severity
            sleep(args.retry_delay)


def list_lights(b: Bridge):
    logging.debug(f'Getting list of lights...')
    try:
        light_list = b.get_light_objects()
    except Exception as e:
        print(f"Error fetching lights: {e}")
        return

    logging.debug(f'List of lights: {light_list}')
    print(f'Available lights:')
    if light_list is not None:
        for light in light_list:
            print(f'{light.light_id}: {light.name}')
    else:
        print(f'<no lights found>')

def load_config_defaults(cli_args_partial):
    """
    Determines config path and loads values, returning a dict of updates for DEFAULTS.
    """
    config_path = cli_args_partial.configfile or os.environ.get('CONFIGFILE')
    new_defaults = {}

    if config_path:
        if not os.path.exists(config_path):
            print(f"Warning: Configuration file not found at {config_path}")
            return {}

        config = configparser.ConfigParser()
        config.read(config_path)

        # Assume settings are in a [General] or [TradfriHue] section, or check multiple
        # For simplicity, we look for a section named 'TradfriHue' or fall back to 'General'
        section = None
        if 'TradfriHue' in config:
            section = config['TradfriHue']
        elif 'General' in config:
            section = config['General']

        if section:
            # Map config strings to types
            if 'bridge_ip' in section:
                new_defaults['bridge_ip'] = section['bridge_ip']

            if 'username' in section:
                new_defaults['username'] = section['username']

            if 'light_ids' in section:
                # Convert string "1, 2, 3" -> list [1.0, 2.0, 3.0]
                try:
                    ids_str = section['light_ids']
                    # Handle comma or space separation
                    ids = [float(x.strip()) for x in ids_str.replace(',', ' ').split() if x.strip()]
                    new_defaults['light_ids'] = ids
                except ValueError:
                    print("Error parsing light_ids in config file. Ensure they are numbers.")

            if 'poll_time' in section:
                new_defaults['poll_time'] = section.getfloat('poll_time')

            if 'brightness_delay' in section:
                new_defaults['brightness_delay'] = section.getfloat('brightness_delay')

            if 'verbose' in section:
                # config can hold int for verbosity level
                new_defaults['verbose'] = section.getint('verbose')

            if 'max_retries' in section:
                new_defaults['max_retries'] = section.getint('max_retries')

            if 'retry_delay' in section:
                new_defaults['retry_delay'] = section.getint('retry_delay')

    return new_defaults

if __name__ == '__main__':
    # Check for Config File
    conf_parser = argparse.ArgumentParser(add_help=False)
    conf_parser.add_argument('-c', '--configfile', help='Path to configuration file (ini format)')

    # parse_known_args returns found args and the rest of the list
    partial_args, remaining_argv = conf_parser.parse_known_args()

    # Load defaults from config if it exists
    config_defaults = load_config_defaults(partial_args)

    # Merge hardcoded defaults with config defaults
    final_defaults = DEFAULTS.copy()
    final_defaults.update(config_defaults)

    # Main Argument Parsing
    parser = argparse.ArgumentParser(
        description='Workaround script for IKEA Trådfri brightness issue on Philips Hue Bridge.',
        parents=[conf_parser] # Inherit the -c argument so it shows in help
    )

    # Note on Positional Args:
    # We make bridge_ip optional (nargs='?') so it can be omitted if provided in config.
    # However, if overriding light_ids positionally, bridge_ip MUST be provided first.
    parser.add_argument('bridge_ip', nargs='?', help='Hue Bridge IP Address')
    parser.add_argument('light_ids', nargs='*', type=float, help='List of Light IDs (float/int)')

    parser.add_argument('-t', '--poll_time', type=float, help=f'Set how often lights are checked (sec). Default: {final_defaults["poll_time"]}')
    parser.add_argument('-d', '--brightness_delay', type=float, help=f'Wait time after change (sec). Default: {final_defaults["brightness_delay"]}')
    parser.add_argument('-l', '--list', action='store_true', help='List available lights')
    parser.add_argument('-v', '--verbose', action='count', help='Increase verbosity (-v or -vv)')
    parser.add_argument('--max-retries', type=int, help='Max connection retries')
    parser.add_argument('--retry-delay', type=int, help='Delay between retries (sec)')
    parser.add_argument('-u', '--username', help='Hue Bridge Username/API Key')

    # Apply the merged defaults.
    # If the user does NOT provide an arg on CLI, the value from `final_defaults` is used.
    parser.set_defaults(**final_defaults)

    args = parser.parse_args()

    # Set logging level
    # Calculate level: Default 1 (-v) -> 30 (WARNING). -vv -> 20 (INFO)?
    # Adjusting to match original script logic approximately:
    # Original: 40 - (10*args.verbose). If verbose=1 (default), level=30 (WARNING).
    # If verbose=2, level=20 (INFO).
    # Note: The original script default verbose=1 actually resulted in WARNING level (40-10=30).
    verbose_count = args.verbose if args.verbose is not None else 1
    verbose_level = max(10, 40 - (10 * verbose_count))

    logging.basicConfig(level=verbose_level, format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

    logging.info(f'Arguments processed: {args}')

    # Validate Requirements
    if not args.bridge_ip and not args.list:
        parser.error("Bridge IP is required. Provide it via argument 'bridge_ip' or in the config file.")

    if not args.list and not args.light_ids:
        logging.warning("No light IDs provided. Script will run but monitor nothing.")

    # Initialize Bridge
    logging.info(f'Connecting to bridge at {args.bridge_ip}...')
    try:
        # Pass username if we have it (skips ~/.python_hue check if provided)
        b = Bridge(args.bridge_ip, username=args.username)
        b.connect()
        logging.info(f'Connected to the bridge')
    except Exception as e:
        logging.error(f"Failed to connect to bridge: {e}")
        sys.exit(1)
    
    if args.list:
        list_lights(b)
    elif args.light_ids:
        main(b, args)
    else:
        print('No light IDs provided to monitor.')
