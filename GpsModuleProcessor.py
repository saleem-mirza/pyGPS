__author__ = 'Saleem'

import re
import serial


class GPGLL(object):
    latitude = None
    longitude = None


class GPGGA(object):
    time = None
    latitude = None
    longitude = None
    fix_quality = None
    num_satellites = None
    hdop = None
    altitude = None


class GPRMC(object):
    time = None
    validity = None
    latitude = None
    longitude = None
    speed = None
    true_course = None
    date = None
    variation = None


class GPVTG(object):
    track = None
    speed_knots = None
    speed_km = None


class GpsModuleProcessor(object):
    @staticmethod
    def calculate_checksum(data):
        _data = str(data)
        if _data[0] == '$':
            _data = _data[1:].split("*")[0]
        else:
            _data = _data.split("*")[0]

        checksum = 0
        for cIndex in _data:
            checksum ^= ord(cIndex)
        return '%X' % checksum

    def __init__(self):
        self.regexp = re.compile("\\$?(.*)\\*?")
        self.tx_rx = None

    def __del__(self):
        print("Resources closed")

    def open(self, device="", baudrate=38400):
        self.tx_rx = serial.Serial(device, baudrate)
        self.tx_rx.timeout = 0.5
        self.set_gps_baud_rate(baudrate)

    def read_line(self):
        return self.tx_rx.readline().rstrip()

    def write_line(self, data):
        self.tx_rx.flushOutput()
        self.tx_rx.writelines(data)

    # Specify number of time GPS module will return GPGGL, GPRMC, GPVTG, GPGGA, GPGSA, GPGSV nmea statements
    def set_gps_nmea_output(self, gpggl=1, gprmc=1, gpvtg=1, gpgga=1, gpgsa=1, gpgsv=1):
        command_string = "$PMTK314,{0},{1},{2},{3},{4},{5},0,0,0,0,0,0,0,0,0,0,0,1,0*".format(
            gpggl, gprmc,
            gpvtg, gpgga,
            gpgsa, gpgsv
        )
        checksum = GpsModuleProcessor.calculate_checksum(command_string)
        command_string = "{0}{1}".format(command_string, checksum)
        self.write_line(command_string)

    def set_gps_baud_rate(self, baud_rate):
        command_string = "$PMTK251,{0}*".format(baud_rate)
        checksum = GpsModuleProcessor.calculate_checksum(command_string)
        command_string = "{0}{1}".format(command_string, checksum)
        self.write_line(command_string)

    def set_gps_update_rate(self, rate):
        command_string = "$PMTK300,{0},0,0,0,0*".format(int(1000 / rate))
        checksum = GpsModuleProcessor.calculate_checksum(command_string)
        command_string = "{0}{1}".format(command_string, checksum)
        self.write_line(command_string)

