"""
---------------------------------------------------------------------
latrunculi: Subclass of game. Implements game methods for latrunculi.
---------------------------------------------------------------------
"""
import numpy as np
from controller.game import Game
from model.state import State, Action

class Latrunculi(Game):
    size = 8
    init_state = None

    def populate_board(self, seed):
        board = np.zeros((self.size, self.size), 'b')
        num_pieces = int((self.size * self.size) / 2)
        if seed is not None:
            # Generate random positions for pieces
            np.random.seed(seed)
            squares = np.arange(0, self.size * self.size)
            np.random.shuffle(squares)

            # Populate board with equal amount of white and black pieces
            for i in range(num_pieces):
                num = squares[i]
                X = int(num / self.size)
                Y = int(num % self.size)
                piece = 1 if i < num_pieces/2 else -1

                board[X][Y] = piece
        else:
            board[:][0:2] = -1
            board[:][-3:-1] = 1
        self.init_state = State(board, True)

    def __init__(self, size, start_seed=None):
        Game.__init__(self)
        self.size = size
        self.populate_board(start_seed)

    def start_state(self):
        return self.init_state

    def player(self, state):
        pass

    def actions(self, state):
        pass

    def result(self, state, action):
        pass

    def terminal_test(self, state):
        pass

    def utility(self, state, player):
        pass
