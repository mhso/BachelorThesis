"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
from controller.game_ai import GameAI

class MCTS(GameAI):
    """
    Implementation of MCTS. This is implemented in terms
    of the four stages of the algorithm: Selection, Expansion,
    Simulation and Backpropagation.
    """
    def select(self, state):
        pass

    def execute_action(self, state):
        super.__doc__

        return self.game.result(state, None)
