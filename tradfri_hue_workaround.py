#!/usr/bin/env python3

import argparse
import logging
from phue import Bridge
from time import sleep, time

# Default values
poll_default = 0.2
delay_default = 1.2


class TradfriLight():
    def __init__(self, light, brightness_delay=1.0):
        self._light = light
        self._last_brightness = light.brightness
        self._brightness_delay = brightness_delay
        self._has_changed = False
        self._t0 = time()

    def check_and_update(self):
        brightness = self._light.brightness
        if self._last_brightness != brightness:
            logging.info(f'Brightness changed detected for light'
                         f'"{self._light.name}": {self._last_brightness}'
                         f'-> {brightness}')
            self._has_changed = True
            self._t0 = time()

        if self._has_changed and self._t0 + self._brightness_delay < time():
            logging.info(f'Brightness for light "{self._light.name}" set to'
                         f'{brightness}')
            self._light.brightness = brightness
            self._has_changed = False

        self._last_brightness = brightness


def main(bridge, args):
    tradfri_ids = args.light_ids
    light_list = bridge.get_light_objects()
    tradfri_lights = [TradfriLight(l, brightness_delay=args.brightness_delay)
                      for l in light_list if l.light_id in tradfri_ids]

    while True:
        for light in tradfri_lights:
            logging.debug(f'Checking light {light._light.name}')
            light.check_and_update()

        logging.debug(f'Sleeping for {args.poll_time} seconds...')
        sleep(args.poll_time)


def list_lights(b: Bridge):
    logging.debug('Getting list of lights...')
    light_list = b.get_light_objects()
    logging.debug(f'List of lights: {light_list}')
    print('Available lights:')
    if light_list is not None:
        for light in light_list:
            print(f'{light.light_id}: {light.name}')
    else:
        print('<no lights found>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description='Workaround script for IKEA Trådfri brightness issue '
                        'on Philips Hue Bridge. Simply run the script with '
                        'bridge IP and Trådfrid light ID\'s as argument. '
                        'Remember to push the bridge button before starting '
                        'the script the first time')
    parser.add_argument('bridge_ip')
    parser.add_argument('light_ids', nargs='*', type=float)
    parser.add_argument('-t', '--poll_time', default=poll_default, type=float,
                        help=f'Set how often the lights are checked for '
                             f'brightness change. Value in seconds '
                             f'({poll_default})')
    parser.add_argument('-d', '--brightness_delay', type=float,
                        help=f'How long to wait after brightness is attempted '
                             f'changed before actually updating the '
                             f'brightness value in seconds ({delay_default})',
                        default=delay_default)
    parser.add_argument('-l', '--list', action='store_true', required=False,
                        default=False, help='List available lights')
    parser.add_argument('-v', '--verbose', action='count',
                        help='Be more verbose. -vv will print debug messages',
                        default=1)
    args = parser.parse_args()

    # Set logging level based on -v's:
    verbose_level = 40 - (10*args.verbose) if args.verbose > 0 else 0
    logging.basicConfig(level=verbose_level,
                        format='%(asctime)s %(levelname)s %(module)s: '
                               '%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    logging.info(f'Arguments: {args}')

    b = Bridge(args.bridge_ip)
    logging.info('Trying to connect to the bridge...')
    b.connect()
    logging.info('Connected to the bridge')
    logging.info('Fetching the API resource...')
    b.get_api()
    logging.info('API resource acquired')

    if args.list:
        list_lights(b)
    elif len(args.light_ids) > 0:
        main(b, args)
    else:
        print('No light IDs provided')
