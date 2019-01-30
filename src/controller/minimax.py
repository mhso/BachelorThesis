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
        capture_weight = 1
        kill_weight = 3
        player_score = ((state.board == player_piece).sum() * kill_weight) + ((state.board == other_piece*2).sum() * capture_weight)
        other_score = ((state.board == other_piece).sum() * kill_weight) + ((state.board == player_piece*2).sum() * capture_weight)

        return player_score - other_score

    def minimax(self, state, depth, maxing_player, alpha, beta):
        """
        Minimax algorithm with alpha-beta pruning.
        """
        if depth == 0 or self.game.terminal_test(state):
            if not maxing_player:
                state.player = not state.player
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
        depth = 10-self.game.size if self.game.size < 8 else 3
    
        # Traverse possible actions, using minimax to calculate best action to take.
        for action in actions:
            result = self.game.result(state, action)
            value = self.minimax(result, depth, False, -10000, 10000)
            if value > highest_value:
                highest_value = value
                best_action = action
        
        print("Highest worth: {}".format(highest_value))
        print("Action taken: {}".format(best_action))
        return self.game.result(state, best_action)
    
    def __str__(self):
        return "Minimax Algorithm"
