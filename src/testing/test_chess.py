from testing import assertion
from controller.chess import Chess
from model.state import Action, State
from util.excelUtil import ExcelUtil
from util.sqlUtil import SqlUtil
from numpy.random import uniform
import numpy as np

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
