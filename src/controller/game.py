"""
---------------------------------------------------------------------------------
game: Super class for game. Implements actions, evaluations, terminal tests, etc.
---------------------------------------------------------------------------------
"""
from abc import ABC, abstractmethod

class Game(ABC):
    # Constructor
    def __init__(self):
        # Do stuff.
        pass

    @abstractmethod
    def start_state(self):
        pass

    @abstractmethod
    def player(self, state):
        pass

    @abstractmethod
    def actions(self, state):
        pass

    @abstractmethod
    def result(self, state, action):
        pass

    @abstractmethod
    def terminal_test(self, state):
        pass

    @abstractmethod
    def utility(self, state, player):
        pass