# -*- coding: utf-8 -*-
# :Project:   LasarApp -- serial communication management
# :Created:   Sun Mar 18 18:04:23 2012 +0100
# :Author:    Stefan Hechenberger <stefan@nortd.com>
# :License:   GNU General Public License version 3 or later
# :Copyright: © 2012-2016 Stefan Hechenberger <stefan@nortd.com> and others,
#             see AUTHORS.txt
#

import os
import sys
import time
import serial
from serial.tools import list_ports


class SerialManagerClass:

    def __init__(self):
        self.device = None

        self.rx_buffer = bytearray()
        self.tx_buffer = bytearray()
        self.tx_index = 0
        self.remoteXON = True

        # TX_CHUNK_SIZE - this is the number of bytes to be
        # written to the device in one go. It needs to match the device.
        self.TX_CHUNK_SIZE = 16
        self.RX_CHUNK_SIZE = 16
        self.nRequested = 0

        # used for calculating percentage done
        self.job_active = False

        # status flags
        self.status = {}
        self.reset_status()

        self.LASAURGRBL_FIRST_STRING = b"LasaurGrbl"

        self.fec_redundancy = 2  # use forward error correction
        # self.fec_redundancy = 1  # use error detection

        self.ready_char = b'\x12'
        self.request_ready_char = b'\x14'
        self.last_request_ready = 0



    def reset_status(self):
        self.status = {
            'ready': True,  # turns True by querying status
            'paused': False,  # this is also a control flag
            'buffer_overflow': False,
            'transmission_error': False,
            'bad_number_format_error': False,
            'expected_command_letter_error': False,
            'unsupported_statement_error': False,
            'power_off': False,
            'limit_hit': False,
            'serial_stop_request': False,
            'door_open': False,
            'chiller_off': False,
            'x': False,
            'y': False,
            'firmware_version': None
        }



    def list_devices(self, baudrate):
        ports = []
        if os.name == 'posix':
            iterator = sorted(list_ports.grep('tty'))
            print("Found ports:")
            for port, desc, hwid in iterator:
                ports.append(port)
                print("%-20s" % (port,))
                print("    desc: %s" % (desc,))
                print("    hwid: %s" % (hwid,))
        else:
            # iterator = sorted(list_ports.grep(''))  # does not return USB-style
            # scan for available ports. return a list of tuples (num, name)
            available = []
            for i in range(24):
                try:
                    s = serial.Serial(port=i, baudrate=baudrate)
                    ports.append(s.portstr)
                    available.append( (i, s.portstr))
                    s.close()
                except serial.SerialException:
                    pass
            print("Found ports:")
            for n,s in available: print("(%d) %s" % (n,s))
        return ports



    def match_device(self, search_regex, baudrate):
        if os.name == 'posix':
            matched_ports = list_ports.grep(search_regex)
            if matched_ports:
                for match_tuple in matched_ports:
                    if match_tuple:
                        return match_tuple[0]
            print("No serial port match for anything like: " + search_regex)
            return None
        else:
            # windows hack because pyserial does not enumerate USB-style com ports
            print("Trying to find Controller ...")
            for i in range(24):
                try:
                    s = serial.Serial(port=i, baudrate=baudrate, timeout=2.0)
                    lasaur_hello = s.read(32)
                    if lasaur_hello.find(self.LASAURGRBL_FIRST_STRING) > -1:
                        return s.portstr
                    s.close()
                except serial.SerialException:
                    pass
            return None


    def connect(self, port, baudrate):
        self.rx_buffer = bytearray()
        self.tx_buffer = bytearray()
        self.tx_index = 0
        self.remoteXON = True
        self.reset_status()

        # Create serial device with both read timeout set to 0.
        # This results in the read() being non-blocking
        # Write on the other hand uses a large timeout but should not be blocking
        # much because we ask it only to write TX_CHUNK_SIZE at a time.
        # BUG WARNING: the pyserial write function does not report how
        # many bytes were actually written if this is different from requested.
        # Work around: use a big enough timeout and a small enough chunk size.
        self.device = serial.Serial(port, baudrate, timeout=0, writeTimeout=1)


    def close(self):
        if self.device:
            try:
                self.device.flushOutput()
                self.device.flushInput()
                self.device.close()
                self.device = None
            except:
                self.device = None
            self.status['ready'] = False
            return True
        else:
            return False

    def is_connected(self):
        return bool(self.device)

    def get_hardware_status(self):
        if self.is_queue_empty():
            # trigger a status report
            # will update for the next status request
            self.queue_gcode(b'?')
        return self.status


    def flush_input(self):
        if self.device:
            self.device.flushInput()

    def flush_output(self):
        if self.device:
            self.device.flushOutput()


    def queue_gcode(self, gcode):
        if isinstance(gcode, str):
            gcode = gcode.encode('utf-8')
        lines = gcode.split(b'\n')
        print("Adding to queue %s lines" % len(lines))
        job_list = []
        for line in lines:
            line = line.strip()
            if line == b'' or line[0] == b'%':
                continue

            if line[0] == b'!':
                self.cancel_queue()
                self.reset_status()
                job_list.append(b'!')
            else:
                if line != b'?':  # not ready unless just a ?-query
                    self.status['ready'] = False

                if self.fec_redundancy > 0:  # using error correction
                    # prepend marker and checksum
                    checksum = 0
                    for c in line:
                        if c > ord(b' ') and c != ord(b'~') and c != ord(b'!'):  #ignore 32 and lower, ~, !
                            checksum += c
                            if checksum >= 128:
                                checksum -= 128
                    checksum = (checksum >> 1) + 128
                    line_redundant = bytearray()
                    for n in range(self.fec_redundancy - 1):
                        line_redundant += b'^' + bytes([checksum]) + line + b'\n'
                    line = line_redundant + b'*' + bytes([checksum]) + line

                job_list.append(line)

        gcode_processed = b'\n'.join(job_list) + b'\n'
        self.tx_buffer += gcode_processed
        self.job_active = True


    def cancel_queue(self):
        self.tx_buffer = bytearray()
        self.tx_index = 0
        self.job_active = False


    def is_queue_empty(self):
        return self.tx_index >= len(self.tx_buffer)


    def get_queue_percentage_done(self):
        buflen = len(self.tx_buffer)
        if buflen == 0:
            return ""
        return str(100 * self.tx_index / float(buflen))


    def set_pause(self, flag):
        # returns pause status
        if self.is_queue_empty():
            return False
        else:
            if flag:  # pause
                self.status['paused'] = True
                return True
            else:     # unpause
                self.status['paused'] = False
                return False


    def send_queue_as_ready(self):
        """Continuously call this to keep processing queue."""
        if self.device and not self.status['paused']:
            try:
                ### receiving
                chars = self.device.read(self.RX_CHUNK_SIZE)
                if len(chars) > 0:
                    ## check for data request
                    if self.ready_char in chars:
                        # print "=========================== READY"
                        self.nRequested = self.TX_CHUNK_SIZE
                        #remove control chars
                        chars = chars.replace(self.ready_char, b'')
                    ## assemble lines
                    self.rx_buffer += chars
                    while(1):  # process all lines in buffer
                        posNewline = self.rx_buffer.find(b'\n')
                        if posNewline == -1:
                            break  # no more complete lines
                        else:  # we got a line
                            line = self.rx_buffer[:posNewline]
                            self.rx_buffer = self.rx_buffer[posNewline + 1:]
                        self.process_status_line(line)
                else:
                    if self.nRequested == 0:
                        time.sleep(0.001)  # no rx/tx, rest a bit

                ### sending
                if self.tx_index < len(self.tx_buffer):
                    if self.nRequested > 0:
                        try:
                            t_prewrite = time.time()
                            actuallySent = self.device.write(
                                self.tx_buffer[self.tx_index:self.tx_index + self.nRequested])
                            if time.time()-t_prewrite > 0.02:
                                sys.stdout.write("WARN: write delay 1\n")
                                sys.stdout.flush()
                        except serial.SerialTimeoutException:
                            # skip, report
                            actuallySent = 0  # assume nothing has been sent
                            sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError\n")
                            sys.stdout.flush()
                        self.tx_index += actuallySent
                        self.nRequested -= actuallySent
                        if self.nRequested <= 0:
                            self.last_request_ready = 0  # make sure to request ready
                    elif self.tx_buffer[self.tx_index] in [b'!', b'~']:  # send control chars no matter what
                        try:
                            t_prewrite = time.time()
                            actuallySent = self.device.write(self.tx_buffer[self.tx_index])
                            if time.time()-t_prewrite > 0.02:
                                sys.stdout.write("WARN: write delay 2\n")
                                sys.stdout.flush()
                        except serial.SerialTimeoutException:
                            actuallySent = 0  # assume nothing has been sent
                            sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError\n")
                            sys.stdout.flush()
                        self.tx_index += actuallySent
                    else:
                        if (time.time()-self.last_request_ready) > 2.0:
                            # ask to send a ready byte
                            # only ask for this when sending is on hold
                            # only ask once (and after a big time out)
                            # print "=========================== REQUEST READY"
                            try:
                                t_prewrite = time.time()
                                actuallySent = self.device.write(self.request_ready_char)
                                if time.time()-t_prewrite > 0.02:
                                    sys.stdout.write("WARN: write delay 3\n")
                                    sys.stdout.flush()
                            except serial.SerialTimeoutException:
                                # skip, report
                                actuallySent = self.nRequested  # pyserial does not report this sufficiently
                                sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError, on ready request\n")
                                sys.stdout.flush()
                            if actuallySent == 1:
                                self.last_request_ready = time.time()

                else:
                    if self.job_active:
                        # print "\nG-code stream finished!"
                        # print "(LasaurGrbl may take some extra time to finalize)"
                        self.tx_buffer = ""
                        self.tx_index = 0
                        self.job_active = False
                        # ready whenever a job is done, including a status request via '?'
                        self.status['ready'] = True
            except OSError:
                # Serial port appears closed => reset
                self.close()
            except ValueError:
                # Serial port appears closed => reset
                self.close()
        else:
            # serial disconnected
            self.status['ready'] = False



    def process_status_line(self, line):
        if b'#' in line[:3]:
            # print and ignore
            sys.stdout.write(line.decode('utf-8') + '\n')
            sys.stdout.flush()
        elif b'^' in line:
            sys.stdout.write("\nFEC Correction!\n")
            sys.stdout.flush()
        else:
            if b'!' in line:
                # in stop mode
                self.cancel_queue()
                # not ready whenever in stop mode
                self.status['ready'] = False
                sys.stdout.write(line.decode('utf-8') + "\n")
                sys.stdout.flush()
            else:
                sys.stdout.write(".")
                sys.stdout.flush()

            if b'N' in line:
                self.status['bad_number_format_error'] = True
            if b'E' in line:
                self.status['expected_command_letter_error'] = True
            if b'U' in line:
                self.status['unsupported_statement_error'] = True

            if b'B' in line:  # Stop: Buffer Overflow
                self.status['buffer_overflow'] = True
            else:
                self.status['buffer_overflow'] = False

            if b'T' in line:  # Stop: Transmission Error
                self.status['transmission_error'] = True
            else:
                self.status['transmission_error'] = False

            if b'P' in line:  # Stop: Power is off
                self.status['power_off'] = True
            else:
                self.status['power_off'] = False

            if b'L' in line:  # Stop: A limit was hit
                self.status['limit_hit'] = True
            else:
                self.status['limit_hit'] = False

            if b'R' in line:  # Stop: by serial requested
                self.status['serial_stop_request'] = True
            else:
                self.status['serial_stop_request'] = False

            if b'D' in line:  # Warning: Door Open
                self.status['door_open'] = True
            else:
                self.status['door_open'] = False

            if b'C' in line:  # Warning: Chiller Off
                self.status['chiller_off'] = True
            else:
                self.status['chiller_off'] = False

            if b'X' in line:
                self.status['x'] = line[line.find(b'X') + 1:line.find(b'Y')].decode('utf-8')
            # else:
            #     self.status['x'] = False

            if b'Y' in line:
                self.status['y'] = line[line.find(b'Y') + 1:line.find(b'V')].decode('utf-8')
            # else:
            #     self.status['y'] = False

            if b'V' in line:
                self.status['firmware_version'] = line[line.find(b'V') + 1:].decode('utf-8')





# singelton
SerialManager = SerialManagerClass()
