from time import time
import numpy as np
from testing import assertion
from controller.chess import Chess
from model.state import Action, State
from util.excelUtil import ExcelUtil
from util.sqlUtil import SqlUtil
from numpy.random import uniform

def run_tests():
    # Test check.
    game = Chess(8)
    board = np.zeros((8, 8))
    board[4, 2] = -Chess.PIDS["R"]
    board[4, 6] = Chess.PIDS["KI"]
    board[1, 1] = Chess.PIDS["P"]
    board[2, 4] = Chess.PIDS["Q"]
    pieces = [(4, 2), (4, 6), (1, 1), (2, 4)]

    state = State(board, True, pieces)

    actions = game.actions(state)

    # ==========================
    # Terminal test
    state = game.start_state()

    print(game.structure_data(state))

def run_iteration_timing_test(log_type=None):
    # TEST STUFF
    print("run iteration timing test Chess")
    game = Chess(8)
    state = game.start_state()

    time_b = time()

    counter = 0
    while counter < 3000:
        actions = game.actions(state)
        action = actions[int(uniform(0, len(actions)))]
        result = game.result(state, action)
        counter += 1

    time_taken = time() - time_b
    print("Time taken to play out game: {} s".format(time_taken))
    print("Iterations: {}".format(counter))

    return time_taken
