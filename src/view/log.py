"""
------------------------------------------------------------------------
log: Log stuff, models (neural & mcts) and board to console and/or file.
------------------------------------------------------------------------
"""
from sys import argv
from time import time
import os
import datetime
import math
from config import Config

debug = "-v" in argv

def log(val):
    global debug
    if debug:
        print(val, flush=True)

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

class FancyLogger:
    game_name = ""
    board_size = 4
    network_status = ""
    thread_statuses = dict()
    train_step = 0
    train_ratio = 0
    performance_values = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
    total_games = 0
    time_started = 0
    eval_checkpoint = 0

    @staticmethod
    def start_timing():
        FancyLogger.time_started = time()

    @staticmethod
    def set_game_and_size(game, size):
        FancyLogger.game_name = game
        FancyLogger.board_size = size
        FancyLogger.pp()

    @staticmethod
    def set_network_status(status):
        FancyLogger.network_status = status
        FancyLogger.pp()

    @staticmethod
    def set_training_step(step):
        FancyLogger.train_step = step
        FancyLogger.train_ratio = step / Config.TRAINING_STEPS
        FancyLogger.pp()

    @staticmethod
    def set_thread_status(thread_id, status):
        FancyLogger.thread_statuses[thread_id] = status
        FancyLogger.pp()

    @staticmethod
    def set_performance_values(values):
        for i, val in enumerate(values):
            if val is not None:
                FancyLogger.performance_values[i] = [int(v * 100) for v in val]
        FancyLogger.pp()

    @staticmethod
    def increment_total_games():
        FancyLogger.total_games += 1
        FancyLogger.pp()

    @staticmethod
    def pp():
        global debug
        if not debug:
            clear_console()
            print("-=-=- Network status -=-=-")
            network_string = f"Network is using {Config.CONV_FILTERS} conv filters, "
            network_string += f"{Config.RES_LAYERS} residual layers, "
            network_string += f"a batch size of {Config.BATCH_SIZE}, "
            network_string += f"and is targeting '{Config.TARGET_VAL}' value."
            print(network_string)
            print(FancyLogger.network_status)

            num_symbols = int(20 * FancyLogger.train_ratio)
            progress_str = "▓" * num_symbols
            remain = "▒" * (20 - num_symbols)
            print("Training progress: {} {}/{}".format(progress_str + remain, FancyLogger.train_step, Config.TRAINING_STEPS))
            print("")

            print("-=-=- Latest evaluation statuses -=-=-")
            perf_rand = FancyLogger.performance_values[0]
            print("Against Random: {}%. As White: {}%. As Black: {}%.".format(perf_rand[0], perf_rand[1], perf_rand[2]))
            perf_mini = FancyLogger.performance_values[1]
            print("Against Minimax: {}%. As White: {}%. As Black: {}%.".format(perf_mini[0], perf_mini[1], perf_mini[2]))
            perf_mcts = FancyLogger.performance_values[2]
            print("Against base MCTS: {}%. As White: {}%. As Black: {}%.".format(perf_mcts[0], perf_mcts[1], perf_mcts[2]))
            perf_macro = FancyLogger.performance_values[3]
            print("Against previous macro network: {}%. As White: {}%. As Black: {}%.".format(perf_macro[0], perf_macro[1], perf_macro[2]))
            print(f"Evaluating {Config.EVAL_GAMES} times every {FancyLogger.eval_checkpoint}th training step.")

            print("")
            print("-=-=- Self play status -=-=-")
            print("Playing {} on a {}x{} board.".format(FancyLogger.game_name, FancyLogger.board_size, FancyLogger.board_size))
            print("MCTS is using {} iterations.".format(Config.MCTS_ITERATIONS))
            print("----------")
            for thread, status in FancyLogger.thread_statuses.items():
                print("{}: {}".format(thread, status))

            print("----------")
            print("Number of actors: {}.".format(Config.ACTORS))
            print(f"Total games generated: {FancyLogger.total_games}.")
            max_buffer = Config.MAX_GAME_STORAGE + (FancyLogger.train_step * Config.MAX_GAME_GROWTH)
            print(f"Max buffer size: {max_buffer}.")
            time_spent = time() - FancyLogger.time_started
            print("Time spent: {0:.3f} s [{1}]".format(time_spent, datetime.timedelta(seconds=math.ceil(time_spent))))
