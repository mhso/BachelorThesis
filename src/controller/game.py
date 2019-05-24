"""
---------------------------------------------------------------------------------
game: Super class for game. Implements actions, evaluations, terminal tests, etc.
---------------------------------------------------------------------------------
"""
from abc import ABC, abstractmethod
from config import Config

class Game(ABC):
    __observers = []
    action_type = "single"

    def __init__(self, size, history=None, q_value_history=None, val_type=None):
        self.size = size
        self.history = history or [self.start_state()]
        self.visit_counts = []
        self.num_actions = 0 # Overriden in subclasses.
        self.__observers = []
        self.q_value_history = q_value_history or []
        self.terminal_value = 0
        self.val_type = val_type or "z"

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
    def map_actions(self, actions, logits):
        """
        Returns a mapping between the given actions and logits and
        normalizes the logits based on which ones represent legal actions.
        """
        pass
    
    @abstractmethod
    def map_visits(self, visits):
        """
        Returns a tensor (of game-specific size/shape) for the network to train on,
        with visit probabilities for each action in the provided dictionary.
        """
        pass

    def clone(self):
        """
        Clones the game and returns it
        """
        game_clone = self.__class__(self.size)
        game_clone.history = [s for s in self.history]
        game_clone.visit_counts = [v for v in self.visit_counts]
        game_clone.q_value_history = [q for q in self.q_value_history]
        game_clone.terminal_value = self.terminal_value
        game_clone.val_type = self.val_type
        return game_clone

    def make_target(self, state_index, training_step=None):
        """
        Return terminal value of given state at index, as well as
        probability distribution for actions at that state.
        The value depends on the arguments given.
        """
        player = self.history[state_index].player
        term_val = self.terminal_value
        z_val = term_val if player or term_val == 0 else -term_val
        if self.val_type == "z":
            # Use 'z' value. Traditional terminal value of game
            # (1 = white wins, -1 = black wins, 0 = draw).
            target_val = z_val
        if self.val_type == "q":
            # Use 'q' value instead of 'z'. This is MCTS's predicted value for the state.
            target_val = self.q_value_history[state_index]
        elif self.val_type == "avg":
            # Use average of 'q' and 'z' value.
            target_val = (z_val + self.q_value_history[state_index]) / 2
        elif self.val_type == "mixed" and training_step is not None:
            # Use linear fall-off of 'z' and 'q' value.
            # This means that 'q' is weighed higher, the larger the current epoch,
            # and 'z' is weighed lower.
            if training_step < Config.Q_LINEAR_FALLOFF:
                ratio = training_step / Config.Q_LINEAR_FALLOFF
                z_val *= (1 - ratio)
                q_val = self.q_value_history[state_index] * ratio
                target_val = z_val + q_val
            else:
                target_val = self.q_value_history[state_index]
        return (target_val, self.visit_counts[state_index])

    def store_search_statistics(self, node):
        """
        Stores the visit counts for the children nodes of the given node
        """
        if node.children == {}:
            self.visit_counts.append({None: 1})
            self.q_value_history.append(0)
        else:
            sum_visits = sum(child.visits for child in node.children.values())
            self.visit_counts.append({
                a: node.children[a].visits / sum_visits for a in node.children
            })
            self.q_value_history.append(-node.q_value)

    def store_value_statistics(self, node):
        """
        Stores the q-value for the given node
        """
        if node is None:
            self.q_value_history.append(None)
        else:
            self.q_value_history.append(node.q_value)

    def reset(self):
        """
        Resets the game data
        """
        self.history = [self.start_state()]
        self.visit_counts = []
        self.q_value_history = []
