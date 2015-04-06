__author__ = 'Saleem'

import re
import sqlite3
from datetime import datetime

import serial


class GpsModuleProcessor(object):
    DATABASE_PATH = 'db/nmea.db'

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

    def __init__(self, log=True):
        self.regexp = re.compile("\\$?(.*)\\*?")
        self.regexRMC = re.compile(
            """
                ^\$GPRMC,
                (?P<hhmmss>\d{6}(\.\d{3})),
                ([AV]),
                (?:(\d+)(\d{2}\.\d+)),
                (?P<NS>[NS]),
                (?:(\d+)(\d{2}\.\d+)),
                (?P<EW>[EW]),
                (?P<speed>\d+(\.\d+)),
                (\d+(\.\d+)),
                (?P<date>\d+),
            """
            , re.VERBOSE
        )
        self.tx_rx = None

        if log:
            self.db = sqlite3.connect(self.DATABASE_PATH)
            self.__init_db()

    def __del__(self):
        print("Resources closed")

    def __init_db(self):
        if self.db:
            self.db.execute(
                """
                CREATE TABLE IF NOT EXISTS raw_nmea
                (
                  ID INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                  nmea_statement TEXT NOT NULL
                )
                """
            )

            self.db.execute(
                """
                    CREATE TABLE IF NOT EXISTS route_info
                    (
                      ID INTEGER PRIMARY KEY AUTOINCREMENT,
                      datetime TEXT,
                      lat REAL,
                      long REAL,
                      speed REAL
                    )
                """
            )

            return True
        return False

    def open(self, device="", baudrate=9600):
        self.tx_rx = serial.Serial(device)
        self.tx_rx.timeout = 0.5
        self.set_gps_baud_rate(baudrate)
        self.tx_rx.baudrate = baudrate
        self.tx_rx.flushOutput()
        self.tx_rx.flushInput()

    def read_line(self):
        return self.tx_rx.readline().rstrip()

    def write_line(self, data):
        self.tx_rx.flushOutput()
        self.tx_rx.writelines(data)

    # Specify number of time GPS module will return GPGGL, GPRMC, GPVTG, GPGGA, GPGSA, GPGSV nmea statements
    def set_gps_nmea_output(self, gpggl=0, gprmc=1, gpvtg=0, gpgga=0, gpgsa=0, gpgsv=0):
        command_string = "$PMTK314,{0},{1},{2},{3},{4},{5},0,0,0,0,0,0,0,0,0,0,0,1,0*".format(
            gpggl, gprmc,
            gpvtg, gpgga,
            gpgsa, gpgsv
        )
        checksum = GpsModuleProcessor.calculate_checksum(command_string)
        command_string = "{0}{1}".format(command_string, checksum)
        self.write_line(command_string + "\r\n")

    def set_gps_baud_rate(self, baudrate):
        command_string = "$PMTK251,{0}*".format(baudrate)
        checksum = GpsModuleProcessor.calculate_checksum(command_string)
        command_string = "{0}{1}".format(command_string, checksum)
        self.write_line(command_string + "\r\n")
        self.tx_rx.baudrate = baudrate

    def set_gps_update_rate(self, rate):
        command_string = "$PMTK300,{0},0,0,0,0*".format(int(1000 / rate))
        checksum = GpsModuleProcessor.calculate_checksum(command_string)
        command_string = "{0}{1}".format(command_string, checksum)
        self.write_line(command_string + "\r\n")

    def log_gps_info(self, statement):
        self.db.execute('''INSERT INTO raw_nmea (timestamp, nmea_statement) VALUES (?, ?)''',
                        (datetime.today(), statement))

        # We are interested in GPRMC only. It contains all required components
        if statement.startswith('$GPRMC'):
            match = self.regexRMC.match(statement)
            if match:
                __aa__ = match.groups()
                _time = str(match.group("hhmmss"))
                _date = str(match.group("date"))

                date = datetime(int(_date[4:6]), int(_date[2:4]), int(_date[0:2]),
                                int(_time[0:2]), int(_time[2:4]), int(_time[4:6]))

                lat = float(match.group(4)) + float(match.group(5)) / 60
                if match.group(6) == 'S':
                    lat = lat * -1

                long = float(match.group(7)) + float(match.group(8)) / 60
                if match.group(9) == 'W':
                    long = long * -1

                speed = float(match.group("speed"))

                self.db.execute('''INSERT INTO route_info(datetime, lat, long, speed) VALUES ( ?, ?, ?, ?)''',
                                (date, lat, long, speed))
                self.db.commit()
