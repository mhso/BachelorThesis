"""
---------------------------------------------------------------------------------
game: Super class for game. Implements actions, evaluations, terminal tests, etc.
---------------------------------------------------------------------------------
"""
from abc import ABC, abstractmethod

class Game(ABC):
    __observers = []
    action_type = "single"

    def __init__(self, history=None, q_value_history=None):
        self.history = history or []
        self.visit_counts = []
        self.num_actions = 0 # Overriden in subclasses.
        self.__observers = []
        self.q_value_history = q_value_history or [] #TODO: might need to be given a parameter, same as history...

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

        #uses the average of z-value and q-value, instead of just z-value
        #terminal_state = self.history[-1]
        #return (((self.utility(terminal_state, self.history[state_index].player) + self.q_value_history[state_index]) / 2),
        #        self.visit_counts[state_index])

        terminal_state = self.history[-1]
        return (self.utility(terminal_state, self.history[state_index].player),
                self.visit_counts[state_index])

    def store_search_statistics(self, node):
        """
        Stores the visit counts for the children nodes of the given node
        """
        if node is None:
            self.visit_counts.append({None: 1})
        else:
            sum_visits = sum(child.visits for child in node.children.values())
            self.visit_counts.append({
                a: node.children[a].visits / sum_visits for a in node.children
            })

    def store_value_statistics(self, node):
        """
        Stores the q-value for the given node
        """
        if node is None:
            self.q_value_history.append(None)
        else:
            self.q_value_history.append(node.q_value)

    def store_random_statistics(self, rand_stats):
        self.visit_counts.append(rand_stats)

    def reset(self):
        self.history = []
        self.visit_counts = []
        self.q_value_history = []

    def register_observer(self, observer):
        """
        Registere observers
        """
        self.__observers.append(observer)
