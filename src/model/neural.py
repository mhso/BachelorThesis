"""
-----------------------------
neural: Neural Network stuff.
-----------------------------
"""
from keras.layers import Dense, Dropout, Convolution2D, BatchNormalization, Input, Dense
from keras.layers.core import Activation
from keras.optimizers import SGD
from keras.models import Sequential
from keras.models import save_model, Model
from keras.utils.vis_utils import plot_model
from model.residual import Residual
import constants

class NeuralNetwork:
    """
    The dual policy network, which guides,
    and is trained by, the MCTS algorithm.
    """
    def __init__(self):
        inp = Input((4, 4, 2, constants.BATCH_SIZE))
        # -=-=-=-=-=- Network 'body'. -=-=-=-=-=-
        # First convolutional layer.
        out = Convolution2D(256, 3, 1, input_shape=(4, 4, 2))(inp)
        out = BatchNormalization()(out)
        out = Activation("relu")(out)

        # Residual layers, 19 in total.
        for _ in range(19):
            out = Residual(256, 256, out)

        # -=-=-=-=-=- Policy 'head'. -=-=-=-=-=-
        policy = Convolution2D(256, 3, 1)(out)
        policy = BatchNormalization()(policy)
        policy = Activation("relu")(policy)

        policy = Convolution2D(32, 3, 1)(policy) # 32 = action space.
        policy = BatchNormalization()(policy)
        policy = Activation("relu")(policy) # Output of action probability distribution.

        # -=-=-=-=-=- Value 'head'. -=-=-=-=-=-
        value = Convolution2D(1, 1, 1)(out)
        value = BatchNormalization()(value)
        value = Activation("relu")(value)

        value = Dense(256) # Linear layer (I think).
        value = Activation("relu")(value)

        # Final value layer. Outputs probability of win/loss/draw as value between -1 and 1.
        value = Dense(1)
        value = Activation("tanh")(value)

        self.model = Model(inputs=inp, outputs=[policy, value])
        self.model.compile(optimizer=SGD(lr=constants.LEARNING_RATES,
                                    decay=constants.WEIGHT_DECAY,
                                    momentum=constants.MOMENTUM),
                                    loss='mean_squared_error')

        plot_model(self.model, to_file='/resources/model_graph.png', show_shapes=True)

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
