"""
---------------------------------------------------------------------------------
game_ai: Super class for any game playing algorithm, e.g: Minimax and MCTS.
---------------------------------------------------------------------------------
"""
from abc import ABC, abstractmethod

class GameAI(ABC):
    @abstractmethod
    def execute_action(self):
        """
        Execute an action or move and return the resulting state.
        """
        pass
