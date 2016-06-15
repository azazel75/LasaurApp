# -*- coding: utf-8 -*-
# :Project:   LasaurApp -- Code run with "py -m backend"
# :Created:   lun 13 giu 2016 17:59:02 CEST
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2016 Stefan Hechenberger <stefan@nortd.com> and others, see AUTHORS.txt
#

import argparse
import logging

def setup_logging():
    "Configure application logging."

    level = logging.DEBUG if __debug__ else logging.INFO
    logging.basicConfig(level=level,
                        format='%(asctime)-15s:%(levelname)-5s: %(message)s')
    log = logging.getLogger(__name__)
    log.debug('Debug log')
    log.info('Info log')
    log.warn('Warn log')
    log.error('Error log')

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='Run LasaurApp.',
                                        prog='lasaurapp')
    argparser.add_argument('port', metavar='serial_port', nargs='?', default=False,
                           help='serial port to the Lasersaur')
    argparser.add_argument('-v', '--version', action='version',
                           version='%(prog)s ' + __version__)
    argparser.add_argument('-p', '--public', dest='host_on_all_interfaces',
                           action='store_true', default=False,
                           help='bind to all network devices (default: bind to '
                           '127.0.0.1)')
    argparser.add_argument('-f', '--flash', dest='flash', action='store_true',
                           default=False, help='flash Arduino with LasaurGrbl '
                           'firmware')
    argparser.add_argument('-b', '--build', dest='build_flash', action='store_true',
                           default=False, help='build and flash from firmware/src')
    argparser.add_argument('-l', '--list', dest='list_serial_devices',
                           action='store_true', default=False, help='list all '
                           'serial devices currently connected')
    argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                           default=False, help='print more verbose for debugging')
    argparser.add_argument('--beaglebone', dest='beaglebone', action='store_true',
                           default=False, help='use this for running on beaglebone')
    argparser.add_argument('--raspberrypi', dest='raspberrypi', action='store_true',
                           default=False, help='use this for running on Raspberry Pi')
    argparser.add_argument('-m', '--match', dest='match',
                           default=GUESS_PREFIX, help='match serial device with '
                           'this string')
    argparser.add_argument('-s', '--syslog', dest='syslog', action='store_true',
                           default=False, help='send log messages to Syslog '
                           'service')
    args = argparser.parse_args()
    setup_logging(args.debug, args.syslog)
    from . import app
    app.main(args)
