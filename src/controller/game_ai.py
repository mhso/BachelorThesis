"""
---------------------------------------------------------------------------------
game_ai: Super class for any game playing algorithm, e.g: Minimax and MCTS.
---------------------------------------------------------------------------------
"""
from abc import ABC, abstractmethod

class GameAI(ABC):
    game = None

    def __init__(self, game):
        self.game = game

    @abstractmethod
    def execute_action(self, state):
        """
        Execute an action or move and return the resulting state.
        """
        pass
