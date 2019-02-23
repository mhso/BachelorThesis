"""
---------------------------------------------------------------------------------
game: Super class for game. Implements actions, evaluations, terminal tests, etc.
---------------------------------------------------------------------------------
"""
from abc import ABC, abstractmethod

class Game(ABC):
    __observers = []

    def __init__(self, history=None):
        self.history = history or []
        self.visit_counts = []
        self.num_actions = 0 # Overriden in subclasses.
        self.__observers = []

    @abstractmethod
    def start_state(self):
        """
        Returns starting state for the game.
        """
        pass

    @abstractmethod
    def player(self, state):
        """
        Returns who's turn it is given a state. True for white, False for black.
        """
        pass

    @abstractmethod
    def actions(self, state):
        """
        Return list of legal moves for the given state.
        """
        pass

    @abstractmethod
    def result(self, state, action):
        """
        Returns the state that results from doing action 'a' in state 's'.
        """
        pass

    @abstractmethod
    def terminal_test(self, state):
        """
        Return True if the given state is a terminal state, meaning that the game is over, False otherwise.
        """
        pass

    @abstractmethod
    def utility(self, state, player):
        """
        If the given player has lost, return -1, for draw return 0, for win return 1
        """
        pass

    @abstractmethod
    def structure_data(self, state):
        """
        Return a structuring of the data in the given state at index,
        so that the Neural Network can accept and work with it.
        """
        pass

    @abstractmethod
    def clone(self):
        pass

    def make_target(self, state_index):
        """
        Return terminal value of given state at index, as well as
        probability distribution for actions at that state.
        """
        state = self.history[state_index]
        return (self.utility(state, state.player), self.visit_counts[state_index])


    def store_search_statistics(self, node):
        sum_visits = sum(child.visits for child in node.children.values())
        self.visit_counts.append({
            a: node.children[a].visit_count / sum_visits if a in node.children else 0
            for a in range(self.num_actions)
        })

    def store_random_statistics(self, rand_stats):
        self.visit_counts.append(rand_stats)

    def reset(self):
        self.history = []
        self.visit_counts = []

    def register_observer(self, observer):
        """
        Registere observers
        """
        self.__observers.append(observer)
