"""
minimax: Implements Minimax with Alpha-Beta pruning for playing a game.
"""
from controller.game_ai import GameAI

class Minimax(GameAI):
    def evaluate_board(self, state):
        """
        Very simple heurstic for evaluating worth of board.
        Simply counts the difference in number of pieces of each player.
        """
        player_piece = 1 if state.player else -1
        other_piece = -1 if state.player else 1
        
        return (state.board == player_piece).sum() - (state.board == other_piece).sum()

    def minimax(self, state, depth, maxing_player, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        """
        if depth == 0 or self.game.terminal_test(state):
            return self.evaluate_board(state)

        actions = self.game.actions(state)

        worth = -10000 if maxing_player else 10000
        for action in actions:
            result = self.game.result(state, action)
            next_depth = self.minimax(result, depth-1, not maxing_player, alpha, beta)
            worth = max(next_depth, worth) if maxing_player else min(next_depth, worth)
            if maxing_player:
                alpha = max(alpha, worth)
            else:
                beta = min(beta, worth)

            if beta <= alpha:
                return worth

        return worth

    def execute_action(self, state):
        super.__doc__
        actions = self.game.actions(state)
        best_action = None
        highest_value = -10000
    
        # Traverse possible actions, using minimax to calculate best action to take.
        for action in actions:
            result = self.game.result(state, action)
            value = self.minimax(result, 3, False, -10000, 10000)
            if value > highest_value:
                highest_value = value
                best_action = action

        print("Action taken: {}".format(best_action))
        return self.game.result(state, best_action)
    
    def __str__(self):
        return "Minimax Algorithm"
