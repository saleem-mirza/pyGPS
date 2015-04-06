__author__ = 'Saleem'

from collections import deque
from threading import Thread
import time

from GpsModuleProcessor import GpsModuleProcessor


keep_running = True
nmea_queue = deque(maxlen=1000)


def nmea_reader_thread_proc():
    global keep_running, nmea_queue
    try:
        g = GpsModuleProcessor()
        g.open("/dev/ttyO4")
        g.set_gps_baud_rate(38400)
        g.set_gps_nmea_output(0, 0, 1, 1, 0, 0)
        g.set_gps_update_rate(2)
        nmea_line = ""
        while keep_running:
            nmea_line = g.read_line()
            if nmea_line.startswith("$"):
                nmea_queue.append(nmea_line)
    except Exception as e:
        keep_running = False


def nmea_processor_thread_proc():
    global keep_running, nmea_queue
    while keep_running:
        try:
            elem = nmea_queue.popleft()
            print(elem)
        except IndexError:
            time.sleep(0.5)


nmea_thread = Thread(target=nmea_reader_thread_proc)
nmea_processor = Thread(target=nmea_processor_thread_proc)

nmea_thread.start()
nmea_processor.start()

time.sleep(5)

# g = GpsModuleProcessor()
# g.log_gps_info("$GPRMC,010820.500,A,3858.9209,N,07724.4354,W,0.00,35.25,050415,,,D*47")
keep_running = False
