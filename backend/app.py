import copy
import glob
import json
import logging
import os
import sys
import tempfile
import time
import webbrowser

from bottle import *
from wsgiref.simple_server import WSGIRequestHandler, make_server

from . import __version__, GUESS_PREFIX
from .serial_manager import get_serial_manager
from .flash import flash_upload, reset_atmega
from .build import build_firmware
from .filereaders import read_svg, read_dxf, read_ngc

log = logging.getLogger(__name__)

APPNAME = "lasaurapp"
VERSION = __version__
COMPANY_NAME = "com.nortd.labs"
SERIAL_PORT = None
BITSPERSECOND = 57600
NETWORK_PORT = 4444
HARDWARE = 'x86'  # also: 'beaglebone', 'raspberrypi'
CONFIG_FILE = "lasaurapp.conf"
COOKIE_KEY = 'secret_key_jkn23489hsdf'
FIRMWARE = "LasaurGrbl.hex"
TOLERANCE = 0.08


def resources_dir():
    """This is to be used with all relative file access.
       _MEIPASS is a special location for data files when creating
       standalone, single file python apps with pyInstaller.
       Standalone is created by calling from 'other' directory:
       python pyinstaller/pyinstaller.py --onefile app.spec
    """
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    else:
        # root is one up from this file
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))


def storage_dir():
    directory = ""
    if sys.platform == 'darwin':
        # from AppKit import NSSearchPathForDirectoriesInDomains
        # # NSApplicationSupportDirectory = 14
        # # NSUserDomainMask = 1
        # # True for expanding the tilde into a fully qualified path
        # appdata = path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APPNAME)
        directory = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', COMPANY_NAME, APPNAME)
    elif sys.platform == 'win32':
        directory = os.path.join(os.path.expandvars('%APPDATA%'), COMPANY_NAME, APPNAME)
    else:
        directory = os.path.join(os.path.expanduser('~'), "." + APPNAME)

    if not os.path.exists(directory):
        os.makedirs(directory)

    return directory


class HackedWSGIRequestHandler(WSGIRequestHandler):
    """ This is a heck to solve super slow request handling
    on the BeagleBone and RaspberryPi. The problem is WSGIRequestHandler
    which does a reverse lookup on every request calling gethostbyaddr.
    For some reason this is super slow when connected to the LAN.
    (adding the IP and name of the requester in the /etc/hosts file
    solves the problem but obviously is not practical)
    """
    def address_string(self):
        """Instead of calling getfqdn -> gethostbyaddr we ignore."""
        # return "(a requester)"
        return str(self.client_address[0])

    def log_request(*args, **kw):
        pass


def run_with_callback(host, port):
    """ Start a wsgiref server instance with control over the main loop.
        This is a function that I derived from the bottle.py run()
    """
    serial_manager = get_serial_manager()
    handler = default_app()
    server = make_server(host, port, handler, handler_class=HackedWSGIRequestHandler)
    server.timeout = 0.01
    server.quiet = True
    msg = "Persistent storage root is: %s" % storage_dir()
    print(msg)
    log.info(msg)
    print("-" * 77)
    print("Bottle server starting up ...")
    msg = "Serial is set to %d bps" % BITSPERSECOND
    print(msg)
    log.info(msg)
    print("Point your browser to: ")
    print("http://%s:%d/      (local)" % ('127.0.0.1', port))
    print("Use Ctrl-C to quit.")
    print("-" * 77)
    print()
    # auto-connect on startup
    global SERIAL_PORT
    if not SERIAL_PORT:
        SERIAL_PORT = serial_manager.match_device(GUESS_PREFIX, BITSPERSECOND)
    serial_manager.connect(SERIAL_PORT, BITSPERSECOND)
    # open web-browser
    try:
        webbrowser.open_new_tab('http://127.0.0.1:%s' % port)
        pass
    except webbrowser.Error:
        print("Cannot open Webbrowser, please do so manually.")
    sys.stdout.flush()  # make sure everything gets flushed
    server.timeout = 0
    while 1:
        try:
            serial_manager.send_queue_as_ready()
            server.handle_request()
            time.sleep(0.0004)
        except KeyboardInterrupt:
            break
    print("\nShutting down...")
    log.info("Shutting down...")
    serial_manager.close()




# @route('/longtest')
# def longtest_handler():
#     fp = open("longtest.ngc")
#     for line in fp:
#         SerialManager.queue_gcode_line(line)
#     return "Longtest queued."



@route('/css/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/css'))

@route('/js/:path#.+#')
def static_js_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/js'))

@route('/img/:path#.+#')
def static_img_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/img'))

@route('/favicon.ico')
def favicon_handler():
    return static_file('favicon.ico', root=os.path.join(resources_dir(),
                                                        'frontend/img'))


### LIBRARY

@route('/library/get/:path#.+#')
def static_library_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'library'),
                       mimetype='text/plain')

@route('/library/list')
def library_list_handler():
    # return a json list of file names
    file_list = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(os.path.join(resources_dir(), 'library'))
        file_list = glob.glob('*')
    finally:
        os.chdir(cwd_temp)
    return json.dumps(file_list)



### QUEUE

def encode_filename(name):
    str(time.time()) + '-' + base64.urlsafe_b64encode(name)

def decode_filename(name):
    index = name.find('-')
    return base64.urlsafe_b64decode(name[index+1:])


@route('/queue/get/:name#.+#')
def static_queue_handler(name):
    return static_file(name, root=storage_dir(), mimetype='text/plain')


@route('/queue/list')
def library_list_handler():
    # base64.urlsafe_b64encode()
    # base64.urlsafe_b64decode()
    # return a json list of file names
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(storage_dir())
        files = list(filter(os.path.isfile, glob.glob("*")))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    return json.dumps(files)

@route('/queue/save', method='POST')
def queue_save_handler():
    ret = '0'
    if 'job_name' in request.forms and 'job_data' in request.forms:
        name = request.forms.get('job_name')
        job_data = request.forms.get('job_data')
        filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
        if os.path.exists(filename) or os.path.exists(filename+'.starred'):
            return "file_exists"
        try:
            fp = open(filename, 'w')
            fp.write(job_data)
            log.info("File saved: %s", filename)
            ret = '1'
        finally:
            fp.close()
    else:
        log.error("Save failed, invalid POST request")
    return ret

@route('/queue/rm/:name')
def queue_rm_handler(name):
    # delete queue item, on success return '1'
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename):
            try:
                os.remove(filename);
                log.info("File deleted: %s", filename)
                ret = '1'
            finally:
                pass
    return ret

@route('/queue/clear')
def queue_clear_handler():
    # delete all queue items, on success return '1'
    ret = '0'
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(storage_dir())
        files = list(filter(os.path.isfile, glob.glob("*")))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    for filename in files:
        if not filename.endswith('.starred'):
            filename = os.path.join(storage_dir(), filename)
            try:
                os.remove(filename);
                log.info("File deleted: %s", filename)
                ret = '1'
            finally:
                pass
    return ret

@route('/queue/star/:name')
def queue_star_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename):
            os.rename(filename, filename + '.starred')
            ret = '1'
    return ret

@route('/queue/unstar/:name')
def queue_unstar_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename + '.starred'):
            os.rename(filename + '.starred', filename)
            ret = '1'
    return ret




@route('/')
@route('/index.html')
@route('/app.html')
def default_handler():
    return static_file('app.html', root=os.path.join(resources_dir(), 'frontend') )


@route('/stash_download', method='POST')
def stash_download():
    """Create a download file event from string."""
    filedata = request.forms.get('filedata')
    fp = tempfile.NamedTemporaryFile(mode='w', delete=False)
    filename = fp.name
    with fp:
        fp.write(filedata)
        fp.close()
    log.info("File stashed: %s", os.path.basename(filename))
    return os.path.basename(filename)

@route('/download/:filename/:dlname')
def download(filename, dlname):
    log.info("Return requested file: %s", filename)
    return static_file(filename, root=tempfile.gettempdir(), download=dlname)


@route('/serial/:connect')
def serial_handler(connect):
    serial_manager = get_serial_manager()
    if connect == '1':
        log.debug('Client is asking to connect serial')
        if not serial_manager.is_connected():
            try:
                global SERIAL_PORT, BITSPERSECOND, GUESS_PREFIX
                if not SERIAL_PORT:
                    SERIAL_PORT = serial_manager.match_device(GUESS_PREFIX,
                                                              BITSPERSECOND)
                serial_manager.connect(SERIAL_PORT, BITSPERSECOND)
                ret = "Serial connected to %s:%d.<br>" % (SERIAL_PORT,
                                                          BITSPERSECOND)
                time.sleep(1.0) # allow some time to receive a prompt/welcome
                serial_manager.flush_input()
                serial_manager.flush_output()
                return ret
            except serial.SerialException:
                SERIAL_PORT = None
                log.exception("Failed to connect to serial.")
                return ""
    elif connect == '0':
        log.debug('Client is asking to close serial')
        if serial_manager.is_connected():
            if serial_manager.close(): return "1"
            else: return ""
    elif connect == "2":
        # print 'js is asking if serial connected'
        if serial_manager.is_connected(): return "1"
        else: return ""
    else:
        log.warn('Ambigious connect request from js: %s', connect)
        return ""



@route('/status')
def get_status():
    serial_manager = get_serial_manager()
    status = copy.deepcopy(serial_manager.get_hardware_status())
    status['serial_connected'] = serial_manager.is_connected()
    status['lasaurapp_version'] = VERSION
    return json.dumps(status)


@route('/pause/:flag')
def set_pause(flag):
    """Returns pause status."""
    serial_manager = get_serial_manager()
    if flag == '1':
        if serial_manager.set_pause(True):
            log.info("Pausing ...")
            return '1'
        else:
            return '0'
    elif flag == '0':
        log.info("Resuming ...")
        if serial_manager.set_pause(False):
            return '1'
        else:
            return '0'



@route('/flash_firmware')
@route('/flash_firmware/:firmware_file')
def flash_firmware_handler(firmware_file=FIRMWARE):
    global SERIAL_PORT, GUESS_PREFIX
    serial_manager = get_serial_manager()
    return_code = 1
    if serial_manager.is_connected():
        serial_manager.close()
    # get serial port by url argument
    # e.g: /flash_firmware?port=COM3
    if 'port' in list(request.GET.keys()):
        serial_port = request.GET['port']
        if serial_port[:3] == "COM" or serial_port[:4] == "tty.":
            SERIAL_PORT = serial_port
    # get serial port by enumeration method
    # currenty this works on windows only for updating the firmware
    if not SERIAL_PORT:
        SERIAL_PORT = serial_manager.match_device(GUESS_PREFIX, BITSPERSECOND)
    # resort to brute force methode
    # find available com ports and try them all
    if not SERIAL_PORT:
        comport_list = serial_manager.list_devices(BITSPERSECOND)
        for port in comport_list:
            print("Trying com port: %s" % port)
            return_code = flash_upload(port, resources_dir(), firmware_file,
                                       HARDWARE)
            if return_code == 0:
                print("Success with com port: %s" % port)
                SERIAL_PORT = port
                break
    else:
        return_code = flash_upload(SERIAL_PORT, resources_dir(), firmware_file,
                                   HARDWARE)
    ret = []
    ret.append('Using com port: %s<br>' % (SERIAL_PORT))
    ret.append('Using firmware: %s<br>' % (firmware_file))
    if return_code == 0:
        print("SUCCESS: Arduino appears to be flashed.")
        ret.append('<h2>Successfully Flashed!</h2><br>')
        ret.append('<a href="/">return</a>')
        return ''.join(ret)
    else:
        print("ERROR: Failed to flash Arduino.")
        ret.append('<h2>Flashing Failed!</h2> Check terminal window for possible'
                   ' errors. ')
        ret.append('Most likely LasaurApp could not find the right serial port.')
        ret.append('<br><a href="/flash_firmware/%s">try again</a> or <a href="'
                   '/">return</a><br><br>' % firmware_file)
        if os.name != 'posix':
            ret. append('If you know the COM ports the Arduino is connected to '
                        'you can specifically select it here:')
            for i in range(1,13):
                ret. append('<br><a href="/flash_firmware?port=COM%s">COM%s</a>'\
                            % (i, i))
        return ''.join(ret)


@route('/build_firmware')
def build_firmware_handler():
    ret = []
    buildname = "LasaurGrbl_from_src"
    firmware_dir = os.path.join(resources_dir(), 'firmware')
    source_dir = os.path.join(resources_dir(), 'firmware', 'src')
    return_code = build_firmware(source_dir, firmware_dir, buildname)
    if return_code != 0:
        log.error("Firmware build error")
        ret.append('<h2>FAIL: build error!</h2>')
        ret.append('Syntax error maybe? Try builing in the terminal.')
        ret.append('<br><a href="/">return</a><br><br>')
    else:
        log.info("SUCCESS: firmware built.")
        ret.append('<h2>SUCCESS: new firmware built!</h2>')
        ret.append('<br><a href="/flash_firmware/'+buildname+'.hex">Flash Now!</a><br><br>')
    return ''.join(ret)


@route('/reset_atmega')
def reset_atmega_handler():
    reset_atmega(HARDWARE)
    return '1'


@route('/gcode', method='POST')
def job_submit_handler():
    serial_manager = get_serial_manager()
    job_data = request.forms.get('job_data')
    if job_data and serial_manager.is_connected():
        serial_manager.queue_gcode(job_data)
        return "__ok__"
    else:
        return "serial disconnected"


@route('/queue_pct_done')
def queue_pct_done_handler():
    serial_manager = get_serial_manager()
    return serial_manager.get_queue_percentage_done()


@route('/file_reader', method='POST')
def file_reader():
    """Parse SVG string."""
    filename = request.forms.get('filename')
    filedata = request.forms.get('filedata')
    dimensions = request.forms.get('dimensions')
    try:
        dimensions = json.loads(dimensions)
    except TypeError:
        dimensions = None


    dpi_forced = None
    try:
        dpi_forced = float(request.forms.get('dpi'))
    except:
        pass

    optimize = True
    try:
        optimize = bool(int(request.forms.get('optimize')))
    except:
        pass
    log.info('Start processing file: "%s"', filename)
    log.debug('Dimensions: "%s", dpi: "%s", optimize: "%s"',
              dimensions, dpi_forced, optimize)

    if filename and filedata:
        log.debug("You uploaded %s (%d bytes)", filename, len(filedata))
        if filename[-4:] in ['.dxf', '.DXF']:
            res = read_dxf(filedata, TOLERANCE, optimize)
        elif filename[-4:] in ['.svg', '.SVG']:
            res = read_svg(filedata, dimensions, TOLERANCE, dpi_forced, optimize)
        elif filename[-4:] in ['.ngc', '.NGC']:
            res = read_ngc(filedata, TOLERANCE, optimize)
        else:
            log.error("Unsupported file format")

        jsondata = json.dumps(res)
        log.debug("Returning %d items as %d bytes", len(res['boundarys']),
                  len(jsondata))
        return jsondata
    return "You missed a field."



# def check_user_credentials(username, password):
#     return username in allowed and allowed[username] == password
#
# @route('/login')
# def login():
#     username = request.forms.get('username')
#     password = request.forms.get('password')
#     if check_user_credentials(username, password):
#         response.set_cookie("account", username, secret=COOKIE_KEY)
#         return "Welcome %s! You are now logged in." % username
#     else:
#         return "Login failed."
#
# @route('/logout')
# def login():
#     username = request.forms.get('username')
#     password = request.forms.get('password')
#     if check_user_credentials(username, password):
#         response.delete_cookie("account", username, secret=COOKIE_KEY)
#         return "Welcome %s! You are now logged out." % username
#     else:
#         return "Already logged out."


def main(args):
    global GUESS_PREFIX, SERIAL_PORT, NETWORK_PORT
    # setup argument parser
    serial_manager = get_serial_manager()

    print("LasaurApp %s" % VERSION)

    if args.beaglebone:
        HARDWARE = 'beaglebone'
        NETWORK_PORT = 80
        SERIAL_PORT = "/dev/ttyO1"

        ### if running on beaglebone, setup (pin muxing) and use UART1
        # for details see: http://www.nathandumont.com/node/250
        if os.path.exists("/sys/kernel/debug/omap_mux/uart1_txd"):
            # echo 0 > /sys/kernel/debug/omap_mux/uart1_txd
            fw = file("/sys/kernel/debug/omap_mux/uart1_txd", "w")
            fw.write("%X" % (0))
            fw.close()
            # echo 20 > /sys/kernel/debug/omap_mux/uart1_rxd
            fw = file("/sys/kernel/debug/omap_mux/uart1_rxd", "w")
            fw.write("%X" % ((1 << 5) | 0))
            fw.close()

        ### if running on BBB/Ubuntu 14.04, setup pin muxing UART1
        pin24list = glob.glob("/sys/devices/ocp.*/P9_24_pinmux.*/state")
        for pin24 in pin24list:
            os.system("echo uart > %s" % (pin24))

        pin26list = glob.glob("/sys/devices/ocp.*/P9_26_pinmux.*/state")
        for pin26 in pin26list:
            os.system("echo uart > %s" % (pin26))


        ### Set up atmega328 reset control
        # The reset pin is connected to GPIO2_7 (2*32+7 = 71).
        # Setting it to low triggers a reset.
        # echo 71 > /sys/class/gpio/export

        ### if running on BBB/Ubuntu 14.04, setup pin muxing GPIO2_7 (pin 46)
        pin46list = glob.glob("/sys/devices/ocp.*/P8_46_pinmux.*/state")
        for pin46 in pin46list:
            os.system("echo gpio > %s" % (pin46))

        try:
            fw = file("/sys/class/gpio/export", "w")
            fw.write("%d" % (71))
            fw.close()
        except IOError:
            # probably already exported
            pass
        # set the gpio pin to output
        # echo out > /sys/class/gpio/gpio71/direction
        fw = file("/sys/class/gpio/gpio71/direction", "w")
        fw.write("out")
        fw.close()
        # set the gpio pin high
        # echo 1 > /sys/class/gpio/gpio71/value
        fw = file("/sys/class/gpio/gpio71/value", "w")
        fw.write("1")
        fw.flush()
        fw.close()


        ### Set up atmega328 reset control - BeagleBone Black
        # The reset pin is connected to GPIO2_9 (2*32+9 = 73).
        # Setting it to low triggers a reset.
        # echo 73 > /sys/class/gpio/export

        ### if running on BBB/Ubuntu 14.04, setup pin muxing GPIO2_9 (pin 44)
        pin44list = glob.glob("/sys/devices/ocp.*/P8_44_pinmux.*/state")
        for pin44 in pin44list:
            os.system("echo gpio > %s" % (pin44))

        try:
            fw = file("/sys/class/gpio/export", "w")
            fw.write("%d" % (73))
            fw.close()
        except IOError:
            # probably already exported
            pass
        # set the gpio pin to output
        # echo out > /sys/class/gpio/gpio73/direction
        fw = file("/sys/class/gpio/gpio73/direction", "w")
        fw.write("out")
        fw.close()
        # set the gpio pin high
        # echo 1 > /sys/class/gpio/gpio73/value
        fw = file("/sys/class/gpio/gpio73/value", "w")
        fw.write("1")
        fw.flush()
        fw.close()


        ### read stepper driver configure pin GPIO2_12 (2*32+12 = 76).
        # Low means Geckos, high means SMC11s

        ### if running on BBB/Ubuntu 14.04, setup pin muxing GPIO2_12 (pin 39)
        pin39list = glob.glob("/sys/devices/ocp.*/P8_39_pinmux.*/state")
        for pin39 in pin39list:
            os.system("echo gpio > %s" % (pin39))

        try:
            fw = file("/sys/class/gpio/export", "w")
            fw.write("%d" % (76))
            fw.close()
        except IOError:
            # probably already exported
            pass
        # set the gpio pin to input
        fw = file("/sys/class/gpio/gpio76/direction", "w")
        fw.write("in")
        fw.close()
        # set the gpio pin high
        fw = file("/sys/class/gpio/gpio76/value", "r")
        ret = fw.read()
        fw.close()
        print("Stepper driver configure pin is: %s" % str(ret))

    elif args.raspberrypi:
        HARDWARE = 'raspberrypi'
        NETWORK_PORT = 80
        SERIAL_PORT = "/dev/ttyAMA0"
        import RPi.GPIO as GPIO
        # GPIO.setwarnings(False) # surpress warnings
        GPIO.setmode(GPIO.BCM)  # use chip pin number
        pinSense = 7
        pinReset = 2
        pinExt1 = 3
        pinExt2 = 4
        pinExt3 = 17
        pinTX = 14
        pinRX = 15
        # read sens pin
        GPIO.setup(pinSense, GPIO.IN)
        isSMC11 = GPIO.input(pinSense)
        # atmega reset pin
        GPIO.setup(pinReset, GPIO.OUT)
        GPIO.output(pinReset, GPIO.HIGH)
        # no need to setup the serial pins
        # although /boot/cmdline.txt and /etc/inittab needs
        # to be edited to deactivate the serial terminal login
        # (basically anything related to ttyAMA0)


    if args.list_serial_devices:
        serial_manager.list_devices(BITSPERSECOND)
    else:
        if not SERIAL_PORT:
            if args.port:
                # (1) get the serial device from the argument list
                SERIAL_PORT = args.port
                print("Using serial device '%s' from command line." % SERIAL_PORT)
            else:
                # (2) get the serial device from the config file
                if os.path.isfile(CONFIG_FILE):
                    fp = open(CONFIG_FILE)
                    line = fp.readline().strip()
                    if len(line) > 3:
                        SERIAL_PORT = line
                        print("Using serial device '%s' from '%s'." % (SERIAL_PORT, CONFIG_FILE))

        if not SERIAL_PORT:
            if args.match:
                GUESS_PREFIX = args.match
                SERIAL_PORT = serial_manager.match_device(GUESS_PREFIX, BITSPERSECOND)
                if SERIAL_PORT:
                    print("Using serial device '%s''" % str(SERIAL_PORT))
                    if os.name == 'posix':
                        # not for windows for now
                        print("(first device to match: %s)"  % args.match)
            else:
                SERIAL_PORT = serial_manager.match_device(GUESS_PREFIX, BITSPERSECOND)
                if SERIAL_PORT:
                    print("Using serial device '%s' by best guess." % str(SERIAL_PORT))

        if not SERIAL_PORT:
            print("-----------------------------------------------------------------------------")
            print("WARNING: LasaurApp doesn't know what serial device to connect to!")
            print("Make sure the Lasersaur hardware is connectd to the USB interface.")
            if os.name == 'nt':
                print("ON WINDOWS: You will also need to setup the virtual com port.")
                print("See 'Installing Drivers': http://arduino.cc/en/Guide/Windows")
            print("-----------------------------------------------------------------------------")

        # run
        if args.debug:
            debug(True)
            if hasattr(sys, "_MEIPASS"):
                print("Data root is: %s" % sys._MEIPASS)
        if args.flash:
            return_code = flash_upload(SERIAL_PORT, resources_dir(), FIRMWARE, HARDWARE)
            if return_code == 0:
                print("SUCCESS: Arduino appears to be flashed.")
            else:
                print("ERROR: Failed to flash Arduino.")
        elif args.build_flash:
            # build
            buildname = "LasaurGrbl_from_src"
            firmware_dir = os.path.join(resources_dir(), 'firmware')
            source_dir = os.path.join(resources_dir(), 'firmware', 'src')
            return_code = build_firmware(source_dir, firmware_dir, buildname)
            if return_code != 0:
                print(ret)
            else:
                print("SUCCESS: firmware built.")
                # flash
                return_code = flash_upload(SERIAL_PORT, resources_dir(), FIRMWARE, HARDWARE)
                if return_code == 0:
                    print("SUCCESS: Arduino appears to be flashed.")
                else:
                    print("ERROR: Failed to flash Arduino.")
        else:
            if args.host_on_all_interfaces:
                run_with_callback('', NETWORK_PORT)
            else:
                run_with_callback('127.0.0.1', NETWORK_PORT)
