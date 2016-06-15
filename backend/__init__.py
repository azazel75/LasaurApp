# -*- coding: utf-8 -*-
# :Project:   LasaurApp -- package init
# :Created:   mer 15 giu 2016 02:09:20 CEST
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2016 Stefan Hechenberger <stefan@nortd.com> and others,
#             see AUTHORS.txt
#

import os
import sys

from .version import __version__

if os.name == 'nt': #sys.platform == 'win32':
    GUESS_PREFIX = "Arduino"
elif os.name == 'posix':
    if sys.platform.startswith('linux'):
        GUESS_PREFIX = "2341"  # match by arduino VID
    else:
        GUESS_PREFIX = "tty.usbmodem"
else:
    GUESS_PREFIX = "no prefix"
