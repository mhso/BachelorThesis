"""
-----------------------------
neural: Neural Network stuff.
-----------------------------
"""
from keras.layers import Dense, Dropout, Conv2D, BatchNormalization
from keras.models import Sequential
from keras.models import save_model
from keras.activations import relu

class NeuralNetwork:
    """
    The dual policy network, which guides,
    and is trained by, the MCTS algorithm.
    """
    def __init__(self):
        model = Sequential()
        #model.add(Conv2D(input_shape=(256), kernel_size= activation="relu"))
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
