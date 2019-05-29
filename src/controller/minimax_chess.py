from time import time
from controller.minimax import Minimax

class Minimax_Chess(Minimax):
    def cutoff(self, depth):
        return super().cutoff(depth)# or time() - self.time_started > 10

    def has_connection(self, conv, num_connected):
        return(conv == num_connected).sum() > 0

    def piece_value(self, piece):
        if piece == 1: # Queen.
            return 90
        if piece == 2: # King.
            return 1000
        if piece == 3: # Rook.
            return 50
        if piece in (4, 5): # Knight.
            return 30
        if piece == 6: # Bishop.
            return 10
        return 0

    def evaluate_board(self, state, depth):
        if self.game.terminal_test(state):
            end_util = self.game.utility(state, state.player)
            return end_util * 1000000

        val = 0
        for y, x in state.pieces:
            piece = state.board[y, x]
            piece_val = self.piece_value(abs(piece))
            if state.player:
                val += piece_val if piece > 0 else -piece_val
            else:
                val += piece_val if piece < 0 else -piece_val
        return val
