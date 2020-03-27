from time import time
from numba import jit
from controller.minimax import Minimax

@jit(nopython=True)
def eval_corners(board, player):
    reward = board[0, -1]
    reward += board[0, 0]
    reward += board[-1, -1]
    reward += board[-1, 0]
    return -reward if player == -1 else reward

@jit(nopython=True)
def eval_edges(board, player):
    top_row = (board[0, :]).sum()
    bottom_row = (board[-1, :]).sum()
    left_col = (board[:, 0]).sum()
    right_col = (board[:, -1]).sum()
    reward = top_row + bottom_row + left_col + right_col

    return -reward if player == -1 else reward

@jit(nopython=True)
def eval_pieces(pieces, board, player):
    reward = 0
    for y, x in pieces:
        reward += board[y][x]
    return -reward if player == -1 else reward

@jit(nopython=True)
def eval_jitted(pieces, size, board, player, num_moves):
    piece_sum = len(pieces)
    early_game = size * size * 0.4
    mid_game = size * size * 0.8
    value = 0
    if piece_sum <= early_game:
        value += 1000 * eval_corners(board, player)
        value += 50 * eval_edges(board, player)
        value += 50 * num_moves
    elif mid_game >= piece_sum > early_game:
        value += 1000 * eval_corners(board, player)
        value += 50 * eval_edges(board, player)
        value += 20 * num_moves
        value += 10 * eval_pieces(pieces, board, player)
    else:
        value += 1000 * eval_corners(board, player)
        value += 100 * eval_edges(board, player)
        value += 100 * num_moves
        value += 200 * eval_pieces(pieces, board, player)
    return value

class Minimax_Othello(Minimax):
    def eval_moves(self, state):
        moves_max = len(self.game.actions(state))
        state.player = not state.player
        moves_min = len(self.game.actions(state))
        state.player = not state.player
        return moves_max - moves_min

    def eval_pieces(self, pieces, board, player):
        reward = 0
        for y, x in pieces:
            reward += board[y][x]
        return -reward if player == -1 else reward

    def evaluate_board(self, state, depth):
        player = 1 if state.player else -1
        board = state.board
        num_moves = self.eval_moves(state)
        pieces = state.pieces

        if self.game.terminal_test(state):
            end_util = self.game.utility(state, state.player)
            return end_util * 1000000

        return eval_jitted(pieces, self.game.size, board, player, num_moves)

    def cutoff(self, depth):
        return super().cutoff(depth) or time() - self.time_started > 15
