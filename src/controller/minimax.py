"""
minimax: Implements Minimax with Alpha-Beta pruning for playing a game.
"""
from controller.game_ai import GameAI
from view.log import log
from numba import jit
from sys import argv

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
def evaluate_board_jit_test(board, player, depth, test_version):
    # COMMON VARS
    player_piece = 1 if player else -1
    other_piece = -1 if player else 1
    player_captured = 2 if player else -2
    other_captured = -2 if player else 2
    
    player_pieces = (board == player_piece).sum()
    other_pieces = (board == other_piece).sum()
    captured_enemy = (board == other_captured).sum()
    captured_player = (board == player_captured).sum()
    bonus = 4*(depth+1) if other_pieces <= 1 else 0 # Add a bonus for winning fast
    
    if test_version == "0": # STANDARD
        return evaluate_board_jit(board, player, depth)
    elif test_version == "1":
        capture_weight = 10
        kill_weight = 2
        return eval_test_version_type1(player_pieces, other_pieces, captured_enemy, kill_weight, captured_player, capture_weight, bonus)
    elif test_version == "2":
        capture_weight = 10
        kill_weight = 50
        return eval_test_version_type1(player_pieces, other_pieces, captured_enemy, kill_weight, captured_player, capture_weight, bonus)
    elif test_version == "3":
        capture_weight = 50
        kill_weight = 10
        return eval_test_version_type1(player_pieces, other_pieces, captured_enemy, kill_weight, captured_player, capture_weight, bonus)
    elif test_version == "4":
        capture_weight = 15
        kill_weight = 100
        return eval_test_version_type1(player_pieces, other_pieces, captured_enemy, kill_weight, captured_player, capture_weight, bonus)
    elif test_version == "5":
        capture_weight = 100
        kill_weight = 15
        return eval_test_version_type1(player_pieces, other_pieces, captured_enemy, kill_weight, captured_player, capture_weight, bonus)

@jit(nopython=True)
def eval_test_version_type1(player_pieces, other_pieces, captured_enemy, kill_weight, captured_player, capture_weight, bonus):
    raw_diff = ((player_pieces - other_pieces) - captured_enemy) * kill_weight
    capture_diff = (captured_enemy - captured_player) * capture_weight
    return raw_diff + capture_diff + bonus

# @jit(nopython=True)
# def eval_test_version_type2(player_pieces, other_pieces, captured_enemy, kill_weight, captured_player, capture_weight, bonus):
#     if other_pieces == 0:
#         piece_bonus = int(player_pieces/0.5) * kill_weight
#     else:
#         piece_bonus = int(player_pieces/other_pieces) * kill_weight
#     captured_bonus = int(captured_enemy-captured_player) * capture_weight
#     return piece_bonus + captured_bonus + bonus

@jit(nopython=True)
def minimax_jit(maxing_player, next_depth, worth, alpha, beta):
    worth = max(next_depth, worth) if maxing_player else min(next_depth, worth)
    if maxing_player:
        alpha = max(alpha, worth)
    else:
        beta = min(beta, worth)
    return beta, alpha, worth

class Minimax(GameAI):
    def evaluate_board(self, state, depth):
        if len(argv) > 2 and "-eval" == argv[len(argv)-3]:
            test_version = argv[len(argv)-2]
            return evaluate_board_jit_test(state.board, state.player, depth, test_version)
        else:
            return evaluate_board_jit(state.board, state.player, depth)

    def minimax(self, state, depth, maxing_player, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        """
        if depth == 0 or self.game.terminal_test(state):
            if not maxing_player:
                state.player = not state.player
            return self.evaluate_board(state, depth)

        actions = self.game.actions(state)

        worth = -10000 if maxing_player else 10000
        for action in actions:
            result = self.game.result(state, action)
            next_depth = self.minimax(result, depth-1, not maxing_player, alpha, beta)
            beta, alpha, worth = minimax_jit(maxing_player, next_depth, worth, alpha, beta)

            if beta <= alpha:
                return worth
        return worth

    def execute_action(self, state):
        super.__doc__
        actions = self.game.actions(state)
        best_action = None
        highest_value = -10000
        depth = 10-self.game.size if self.game.size < 8 else 3

        # Traverse possible actions, using minimax to calculate best action to take.
        for action in actions:
            result = self.game.result(state, action)
            value = self.minimax(result, depth, False, -10000, 10000)
            if value > highest_value:
                highest_value = value
                best_action = action

        log("Minimax action: {} worth: {}".format(best_action, highest_value))
        return self.game.result(state, best_action)

    def __str__(self):
        return "Minimax Algorithm"
