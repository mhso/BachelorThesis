"""
minimax: Implements Minimax with Alpha-Beta pruning for playing a game.
"""
from controller.game_ai import GameAI
from view.log import log
from sys import argv
from time import time
from numba import jit

@jit(nopython=True)
def evaluate_board_jit(board, player, depth):
    """
    Very simple heurstic for evaluating worth of board.
    Simply counts the difference in number of pieces of each player.
    """
    player_piece = 1 if player else -1
    other_piece = -1 if player else 1
    player_captured = 2 if player else -2
    other_captured = -2 if player else 2

    player_pieces = (board == player_piece).sum()
    other_pieces = (board == other_piece).sum()
    captured_enemy = (board == other_captured).sum()
    captured_player = (board == player_captured).sum()
    bonus = 4*(depth+1) if other_pieces <= 1 else 0 # Add a bonus for winning fast.

    capture_weight = 2
    kill_weight = 10

    raw_diff = ((player_pieces - other_pieces) - captured_enemy) * kill_weight
    capture_diff = (captured_enemy - captured_player) * capture_weight

    return raw_diff + capture_diff + bonus

@jit(nopython=True)
def minimax_jit(maxing_player, next_depth, worth, alpha, beta):
    """
    jit version of the minimax logic.
    """
    worth = max(next_depth, worth) if maxing_player else min(next_depth, worth)
    if maxing_player:
        alpha = max(alpha, worth)
    else:
        beta = min(beta, worth)
    return beta, alpha, worth

class Minimax(GameAI):
    time_started = 0
    player = None

    def __init__(self, game):
        GameAI.__init__(self, game)
        self.tpt = dict() # Transposition table.

        game_name = type(self.game).__name__
        if game_name == "Latrunculi":
            self.MAX_DEPTH = 12-self.game.size if self.game.size < 8 else 5
        elif game_name == "Connect_Four":
            self.MAX_DEPTH = 13-self.game.size
        elif game_name == "Othello":
            self.MAX_DEPTH = 15-self.game.size
        log(f"Minimax is using a max search depth of {self.MAX_DEPTH}")

    def evaluate_board(self, state, depth):
        """
        Evaluate board using game specific heurstics.
        This class implements Minimax for Latrunculi.
        Minimax implementations for other games (Connect Four,
        Othello) need only derive from this class and overwrite
        this method.
        Some of the logic has been moved to other methods, so they can be jit compiled.
        """
        return evaluate_board_jit(state.board, state.player, depth)

    def cutoff(self, depth):
        return not depth

    def minimax(self, state, depth, maxing_player, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        Some of the logic has been moved to other methods, so they can be jit compiled.
        """
        state_hash = state.stringify()
        val = self.tpt.get(state_hash, None)
        if val is not None:
            return val

        if self.cutoff(depth) or self.game.terminal_test(state):
            if not maxing_player and (self.player != state.player):
                state.player = not state.player
            return self.evaluate_board(state, depth)

        actions = self.game.actions(state)

        worth = -10000 if maxing_player else 10000
        for action in actions:
            result = self.game.result(state, action)
            next_depth = self.minimax(result, depth-1, not maxing_player, alpha, beta)
            beta, alpha, worth = minimax_jit(maxing_player, next_depth, worth, alpha, beta)

            if beta <= alpha:
                break
        self.tpt[state_hash] = worth
        return worth

    def execute_action(self, state):
        super.__doc__
        self.player = state.player
        actions = self.game.actions(state)
        if actions == [None]:
            return self.game.result(state, None)
        best_action = None
        highest_value = -float("inf")

        self.time_started = time()
        # Traverse possible actions, using minimax to calculate best action to take.
        for action in actions:
            result = self.game.result(state, action)
            value = self.minimax(result, self.MAX_DEPTH, False, -10000, 10000)
            if value > highest_value:
                highest_value = value
                best_action = action

        log("Minimax action: {} worth: {}".format(best_action, highest_value))
        return self.game.result(state, best_action)

    def __str__(self):
        return "Minimax Algorithm"
