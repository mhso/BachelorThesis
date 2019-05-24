import numpy as np
from numba import jit
from controller.game import Game
from model.state import State, Action

def actions_king(pieces, board, player_num):
    pass

def actions_queen(pieces, board, player_num):
    pass

def actions_knight(pieces, board, player_num):
    pass

def actions_bishop(pieces, board, player_num):
    pass

def actions_rook(pieces, board, player_num):
    pass

def actions_pawn(pieces, board, player_num):
    pass

class Chess(Game):
    QUEEN = 1
    KING = 2
    ROOK = 3
    KNIGHT = 4
    BISHOP = 5
    PAWN = 6

    def __init__(self, size, rand_seed=None):
        super().__init__(size)
        self.num_actions = 4672

    def start_state(self):
        super.__doc__
        board = np.zeros((self.size, self.size), dtype="b")
        board[0, :] = [-self.ROOK, -self.KNIGHT, -self.BISHOP, -self.QUEEN,
                       -self.KING, -self.BISHOP, -self.KNIGHT, -self.ROOK]
        board[1, :] = [-self.PAWN for _ in range(self.size)]
        board[-1, :] = [self.ROOK, self.KNIGHT, self.BISHOP, self.QUEEN,
                        self.KING, self.BISHOP, self.KNIGHT, self.ROOK]
        board[-2, :] = [self.PAWN for _ in range(self.size)]
        pieces = [(y, x) for y in range(0, self.size, self.size-1) for x in range(self.size)]
        pieces.extend([(y, x) for y in range(1, self.size-1, self.size-3) for x in range(self.size)])
        return State(board, True, pieces)

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        return [None]
        """
        action_coords = []
        player_num = 1 if self.player(state) else -1
        action_coords.extend(actions_king(state.pieces, state.board, player_num))
        action_coords.extend(actions_queen(state.pieces, state.board, player_num))
        action_coords.extend(actions_knight(state.pieces, state.board, player_num))
        action_coords.extend(actions_bishop(state.pieces, state.board, player_num))
        action_coords.extend(actions_rook(state.pieces, state.board, player_num))
        action_coords.extend(actions_pawn(state.pieces, state.board, player_num))
        return [Action((y1, x1), (y2, x2)) for y1, x1, y2, x2 in action_coords]
        """

    def result(self, state, action):
        super.__doc__
        return state

    def terminal_test(self, state):
        super.__doc__
        return True

    def utility(self, state, player):
        super.__doc__
        return 0

    def structure_data(self, state):
        super.__doc__
        return []

    def map_actions(self, actions, logits):
        super.__doc__
        return {}

    def map_visits(self, visits):
        super.__doc__
        return []
