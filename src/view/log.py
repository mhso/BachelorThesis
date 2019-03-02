"""
------------------------------------------------------------------------
log: Log stuff, models (neural & mcts) and board to console and/or file.
------------------------------------------------------------------------
"""
from sys import argv
from time import time
from threading import Lock
import constants
import os

debug = "-v" in argv

def log(val):
    global debug
    if debug:
        print(val, flush=True)

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

class FancyLogger:
    network_status = ""
    thread_statuses = dict()
    train_step = 0
    train_ratio = 0
    performance_values = (0, 0, 0)
    total_games = 0
    time_started = 0
    lock = Lock()

    @staticmethod
    def start_timing():
        FancyLogger.time_started = time()

    @staticmethod
    def set_network_status(status):
        FancyLogger.network_status = status
        FancyLogger.pp()

    @staticmethod
    def set_training_step(step):
        FancyLogger.train_step = step
        FancyLogger.train_ratio = step / constants.TRAINING_STEPS
        FancyLogger.pp()

    @staticmethod
    def set_thread_status(thread_id, status):
        FancyLogger.thread_statuses[thread_id] = status
        FancyLogger.pp()

    @staticmethod
    def set_performance_values(values):
        FancyLogger.performance_values = values
        FancyLogger.pp()

    @staticmethod
    def increment_total_games():
        FancyLogger.total_games += 1
        FancyLogger.pp()

    @staticmethod
    def pp():
        FancyLogger.lock.acquire()
        clear_console()
        print("-=-=- Network status -=-=-")
        print(FancyLogger.network_status)

        num_symbols = constants.TRAINING_STEPS * FancyLogger.train_ratio
        progress_str = "▓" * num_symbols
        remain = "▒" * (20 - num_symbols)
        print("Training progress: {} {}/{}".format(progress_str + remain, FancyLogger.train_step, constants.TRAINING_STEPS))
        print("")

        print("-=-=- Latest evaluation statuses -=-=-")
        print("Against Random: {}".format(FancyLogger.performance_values[0]))
        print("Against Minimax: {}".format(FancyLogger.performance_values[1]))
        print("Against base MCTS: {}".format(FancyLogger.performance_values[2]))
        print("")
        print("-=-=- Self play status -=-=-")
        for thread, status in FancyLogger.thread_statuses.items():
            print("{}: {}".format(thread, status))

        print("Number of processes: {}".format(constants.GAME_THREADS))
        print("Total games generated: {}".format(FancyLogger.total_games))
        print("Time spent: {} s".format(time() - FancyLogger.time_started))
        FancyLogger.lock.release()
