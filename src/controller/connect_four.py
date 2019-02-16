"""
-----------------------------
connect_four: We all know it.
-----------------------------
"""
from controller.game import Game
from model.state import State, Action
from scipy.signal import convolve2d
import numpy as np

class Connect_Four(Game):
    __observers = []

    def __init__(self, size, rand_seed=None):
        self.size = size
        self.terminal_kernels = [
            np.array([[1, 1, 1, 1]]),
            np.array([[1], [1], [1], [1]]),
            np.eye(4, 4),
            np.fliplr(np.eye(4, 4))
        ]

    def start_state(self):
        super.__doc__
        return State(np.zeros((self.size-1, self.size), dtype='b'), True)

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        board = state.board
        action_list = []
        for x in range(0, self.size):
            for y in range(self.size-2, -1, -1):
                if board[y][x] == 0:
                    action_list.append(Action((y, x), None))
                    break
        return action_list

    def result(self, state, action):
        super.__doc__
        y, x = action.source
        copy_arr = np.copy(state.board)
        copy_arr[y][x] = 1 if state.player else -1
        return State(copy_arr, not state.player)

    def terminal_test(self, state):
        super.__doc__
        if (state.board == 0).sum() == 0:
            return True
        for kernel in self.terminal_kernels:
            conv = convolve2d(state.board, kernel, mode="valid")
            if (conv == 4).sum() > 0 or (conv == -4).sum() > 0:
                return True
        return False

    def utility(self, state, player):
        super.__doc__
        for kernel in self.terminal_kernels:
            conv = convolve2d(state.board, kernel, mode="valid")
            if (conv == 4).sum() > 0:
                return 1
            elif (conv == -4).sum() > 0:
                return -1
        return 0

    def structure_data(self, state):
        super.__doc__
        return []
