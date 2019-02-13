from scipy.signal import convolve2d
from controller.minimax import Minimax
from numpy import nditer

class Minimax_CF(Minimax):
    def has_connection(self, conv, num_connected):
        return(conv == num_connected).sum() > 0

    def evaluate_board(self, state, depth):
        val = 0
        for kernel in self.game.terminal_kernels:
            conv = convolve2d(state.board, kernel, mode="valid")
            for i in range(4, 0, -1):
                player = i if state.player else -i
                if self.has_connection(conv, player):
                    val += i * i
                if self.has_connection(conv, -player):
                    val -= i * i
        return val
