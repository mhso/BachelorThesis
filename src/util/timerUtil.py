from time import time
import socket
import datetime

class TimerUtil:

    def __init__(self):
        self.time_started = None
        self.time_end = None 

    def start_timing(self):
        self.time_started = time()
    
    def stop_timing(self):
        self.time_end = time()

    def time_duration(self):
        return self.time_end - self.time_started
    
    def print_start_timing(self, msg):
        print ("{} {} seconds since epoch".format(msg, self.time_started))
    
    def print_stop_timing(self, msg):
        print ("{} {} seconds since epoch".format(msg, self.time_started))

    def print_duration_in_seconds(self, msg):
        print ("{}, duration: {:.1f} seconds".format(msg, self.time_duration()))

    @staticmethod
    def get_computer_hostname():
        hostname = socket.gethostname()
        return hostname

    @staticmethod
    def get_datetime_str():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")