.. -*- coding: utf-8 -*-
.. :Project:   LasarApp -- Introduction
.. :Created:   ven 10 giu 2016 02:57:02 CEST
.. :Author:    Alberto Berti <alberto@metapensiero.it>
.. :License:   GPL3 or later
.. :Copyright: © 2016 Stefan Hechenberger <stefan@nortd.com> and others, see AUTHORS.txt
..

LasaurApp
=========

LasaurApp is the official `Lasersaur`__ app. It
has all the functionality to operate this kind of laser cutter:

- load vector files and send them to the Lasersaur;
- file support for SVG, G-code (subset), DXF (subset);
- GUI widget to move the laser head;
- pausing/continuing a job;
- firmware flashing;
- handy G-code programs for the optics calibration process.

This app is written mostly in cross-platform, cross-browser Javascript
and Python. This allows for very flexible setup. The backend can
either run directly on the Lasersaur (Driveboard) or on the client
computer. The frontend runs in a web browser either on the same client
computer or on a tablet computer.

__ http://lasersaur.com
