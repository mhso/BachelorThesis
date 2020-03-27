"""
---------------------------------------------------------------------------------
game_ai: Super class for any game playing algorithm, e.g: Minimax and MCTS.
---------------------------------------------------------------------------------
"""
from abc import ABC, abstractmethod
from config import Config

class GameAI(ABC):
    game = None

    def __init__(self, game):
        self.game = game
        self.cfg = Config

    def set_config(self, config):
        self.cfg = config

    @abstractmethod
    def execute_action(self, state):
        """
        Execute an action or move and return the resulting state.
        """
