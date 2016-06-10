LasaurApp
=========

LasaurApp is the official `Lasersaur`__ app. It
has all the functionality to operate this kind of laser cutter:

- load vector files and send them to the Lasersaur
- file support for SVG, G-code (subset), DXF (subset)
- GUI widget to move the laser head
- pausing/continuing a job
- firmware flashing
- handy G-code programs for the optics calibration process

__ http://lasersaur.com

This app is written mostly in cross-platform, cross-browser Javascript
and Python. This allows for very flexible setup. The backend can
either run directly on the Lasersaur (Driveboard) or on the client
computer. The frontend runs in a web browser either on the same client
computer or on a tablet computer.

This repository contains experimental code that differs from `the one from
Stefan`__:

- it runs the backend using Python 3 instead of the legacy Python 2;
- all the external dependencies that were imported have been deleted and are
  now installed as dependencies;
- the code has been cleaned up a bit;
- All the prints have been replaced with logging statements so that it's
  possible to debug it or simply serialize the operations performed by the
  cutter to or send them to another host for further processing (still in
  progress).

__ https://github.com/stefanix/LasaurApp

When running on the Driveboard people can start using the 'saur'
directly from their laptop without having to setup any software or
drivers. This is done this way because we imagine laser cutters being
shared in shops. We see people controlling laser cutters from their
laptops and not wanting to go through annoying setup
processes. Besides this, html-based GUIs are just awesome :)

.. DANGER:: Please be aware that operating a self-built laser
   cutter can be dangerous and requires full awareness of the risks
   involved. NORTD Labs does not warrant for any contents of the manual
   and does not assume any risks whatsoever with regard to the contents
   of this manual or the machine assembled by you. NORTD Labs further
   does not warrant for and does not assume any risks whatsoever with
   regard to any parts of the machine contained in this manual which
   are provided by third parties. You need to have the necessary
   experience in handling high-voltage electrical devices and class 4
   laser beams to build the machine described in this manual. Otherwise
   you should seek professional advice for building the machine.


How to Use this App
-------------------

* make sure you have Python 2.7
* run *python backend/app.py*
* The GUI will open in a browser at *http://localhost:4444*
  (supported are Firefox, Chrome, and likely future Safari 6+ or IE 10+)

For more information see the `Lasersaur Software Setup
Guide`__

__ http://www.lasersaur.com/manual/software


Notes on Creating Standalone Apps
----------------------------------

With `PyInstaller`__ it's possible to convert a python app to a standalone,
single file executable. This allows us to make the setup process much easier
and remove all the the prerequisites on the target machine (including python).

__ http://www.pyinstaller.org

From a shell/Terminal do the following:

* go to LasaurApp/other directory
* run 'python pyinstaller/pyinstaller.py --onefile app.spec'
* the executable will be other/dist/lasaurapp (or dist/lasaurapp.exe on Windows)

Most of the setup for making this happen is in the app.spec file. Here
all the accessory data and frontend files are listed for inclusion in
the executable. In the actual code the data root directory can be
found in 'sys._MEIPASS'.


Notes on Testing on a Virtual Windows System
---------------------------------------------

When running VirtualBox on OSX it has troubles accessing the USB port
even when all the VirtualBox settings are correct. This is because OSX
captures the device. To make it available in VirtualBox one has to
unload it in OSX first. The following works for Arduino Unos:

- sudo kextunload -b com.apple.driver.AppleUSBCDC

After the VirtualBox session this can be undone with:

- sudo kextload -b com.apple.driver.AppleUSBCDC

For other USB devices thee following may be useful too:
- sudo kextunload -b com.apple.driver.AppleUSBCDCWCM
- sudo kextunload -b com.apple.driver.AppleUSBCDCACMData
- sudo kextunload -b com.apple.driver.AppleUSBCDCACMControl
