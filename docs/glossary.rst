.. -*- coding: utf-8 -*-
.. :Project:   LasarApp -- Glossary definitions
.. :Created:   ven 10 giu 2016 03:00:03 CEST
.. :Author:    Alberto Berti <alberto@metapensiero.it>
.. :License:   GPL3 or later
.. :Copyright: © 2016 Stefan Hechenberger <stefan@nortd.com> and others, see AUTHORS.txt
..

Glossary of terms
=================

.. glossary::

   ATmega
     The microcontroller controls the `DriveBoard`
     It is an `Atmel ATmega328P`__ chip that integrates a CPU and severarl
     Input/Output subsystems like a serial interface, `PWM` generation and
     analog-to-digital signal conversion.

     __ http://www.mouser.com/ds/2/36/atmel-8271-8-bit-avr-microcontroller-atmega48a-48p-365589.pdf

   backend
     The Python code program that runs on the `BBB` board. It's
     available on the 'backend' subfolder of the repository.

   BBB
      The BeagleBone Black board that runs GNU/Linux and the `backend`
      software and connects to the LAN via its Ethernet socket.

   DriveBoard
     The printed circuit board were all the control logic electronics reside.
     See the `appropriate page on the LaserSaur manual`__

     __ https://github.com/nortd/lasersaur/wiki/driveboard

   firmware
     The C code program that runs on the `ATmega` microcontroller. It's
     available on the 'firmware' subfolder of the repository.

   frontend
     The Javascript code that runs the LasaurApp in the browser. It's
     available on the 'frontend' subfolder of the repository.

   GCODE
     A simple language that defines the atomic operations performed by the
     cutter. This ranges from movements, to the cut operations, to status
     request, to the (dis)abilitation of the various subsystems. See the
     `specific page on the LaserSaur manual`__ for further details.

     __ https://github.com/nortd/lasersaur/wiki/gcode

   Laser Tube
      The CO2 laser generator which is the heart of the LaserSaur.

   PWM
      The `Pulse-Width Modulation`__ is a modulation tecnique where the amplitude (the
      height of the wave form) remains constant and instead the it's the
      *duty-cycle* that may change from a period to another.
      The `ATmega` on the `DriveBoard` is able to emit souch kind of signal
      which can be used to control the power output of the `laser tube`.

      __ https://en.wikipedia.org/wiki/Pulse-width_modulation
