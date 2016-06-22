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
- file support for SVG, `G-code` (subset), DXF (subset);
- GUI widget to move the laser head;
- pausing/continuing a job;
- firmware flashing;
- handy `G-code` programs for the optics calibration process.

This app is written mostly in cross-platform, cross-browser Javascript
and Python. This allows for very flexible setup. The backend can
either run directly on the Lasersaur (Driveboard) or on the client
computer. The frontend runs in a web browser either on the same client
computer or on a tablet computer.

__ http://lasersaur.com

Architecture
============

The software system is comprised of three parts that reside each in its own
directory:

``/firmware``
  Contains the C language sources and the already compiled binaries of the
  modified `grbl`__ `CNC` controller software that is installed on the `ATmega`
  chip that manages all the circuitry on the `DriveBoard`;

``/backend``
  Contains the Python language sources of the service that runs on the `BBB`.
  It communicates on one side via a serial line to the `ATmega` and on the
  other side with the client that runs the GUI in the web browser;

``/frontend``
  Contains the HTML and JavaScript code used to run the GUI in the web
  browser. It communicates with the `backend` using the HTTP protocol.

__ https://github.com/grbl/grbl

Overally the system can be represented in a simple graph as follows:

.. aafig::
   :textual:
   :scale: 80
   :proportional:


                    user

                     ^
                     |
                     |
                     v
               +-----------+
               |   GUI     |
               |           |
               | (frontend)|
               |           |
               |web browser|
               +-----------+
                     ^
                     |
                     |
                     |    HTTP
                     |
                     |
                     v
               +-----------+
               |  service  |
               |           |
               | (backend) |
               |           |
               |    BBB    |
               +-----------+
                     ^
                     |
                     |    serial line
                     |
                     |
                     v
               +-----------+
               |CNC manager|
               |           |
               | (firmware)|
               |           |
               |   ATmega  |
               +-----------+
                     ^
                     |
                     |
                     v

                 lasersaur
