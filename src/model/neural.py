"""
-----------------------------
neural: Neural Network stuff.
-----------------------------
"""
from keras.layers import Dense, Dropout
from keras.models import Sequential
from keras.models import save_model

class NeuralNetwork:
    """
    The dual policy network, which guides,
    and is trained by, the MCTS algorithm.
    """
    def __init__(self):
        pass

    def evaluate(self, state):
        """
        Evaluate a given state using the network.
        @returns (p, z)
        - p: A list of probabilities for each
        available action in state. These values help
        guide the MCTS search.
        - z: A value indicating the expected outcome of
        the game from the given state.
        """
        return None
