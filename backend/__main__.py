# -*- coding: utf-8 -*-
# :Project:   LasaurApp -- Code run with "py -m backend"
# :Created:   lun 13 giu 2016 17:59:02 CEST
# :Author:    Alberto Berti <alberto@metapensiero.it>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2016 Stefan Hechenberger <stefan@nortd.com> and others, see AUTHORS.txt
#

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
    setup_logging()
    from . import app
    app.main()
