from controller.game import Game
from controller.game_ai import GameAI

class Minimax(GameAI):
    game = None

    def __init__(self, game):
        GameAI.__init__(self)
        self.game = game

    def evaluate_board(self, state):
        """
        Very simple heurstic for evaluating worth of board.
        Simply counts the difference in number of pieces of each player.
        """
        player_piece = 1 if state.player else -1
        other_piece = -1 if state.player else 1
        return (state.board == player_piece).sum() - (state.board == other_piece).sum()

    def minimax(self, node, depth, maxing_player, alpha, beta):
        return depth + maxing_player

    def execute_action(self, state):
        super.__doc__
        actions = self.game.actions(state)
        best_action = None
        highest_value = -10000

        # Traverse possible actions, using minimax to calculate best action to take.
        for action in actions:
            result = self.game.result(state, action)
            value = self.minimax(state, 3, True, -10000, 10000)
            if value > highest_value:
                highest_value = value
                best_action = action

        return self.game.result(state, best_action)

    def __str__(self):
        return "Minimax Algorithm"
