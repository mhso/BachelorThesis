"""
-----------------------------
neural: Neural Network stuff.
-----------------------------
"""
from keras.layers import Dense, Dropout, Conv2D, BatchNormalization, Input, Flatten
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
        inp = Input((4, 4, 2,))

        # -=-=-=-=-=- Network 'body'. -=-=-=-=-=-
        # First convolutional layer.
        out = Conv2D(256, kernel_size=3, strides=1, kernel_initializer="random_uniform",
                                                    bias_initializer="random_uniform")(inp)
        out = BatchNormalization()(out)
        out = Activation("relu")(out)

        # Residual layers, 19 in total.
        for _ in range(19):
            out = Residual(256, 256, out)

        # -=-=-=-=-=- Policy 'head'. -=-=-=-=-=-
        policy = Conv2D(256, kernel_size=3, strides=1, padding="same",
                                                    kernel_initializer="random_uniform",
                                                    bias_initializer="random_uniform")(out)
        policy = BatchNormalization()(policy)
        policy = Activation("relu")(policy)

        policy = Conv2D(32, kernel_size=3, strides=1, padding="same",
                                                    kernel_initializer="random_uniform",
                                                    bias_initializer="random_uniform")(policy) # 32 = action space.

        # -=-=-=-=-=- Value 'head'. -=-=-=-=-=-
        value = Conv2D(1, kernel_size=1, strides=1, kernel_initializer="random_uniform",
                                                    bias_initializer="random_uniform")(out)
        value = BatchNormalization()(value)
        value = Activation("relu")(value)

        value = Flatten()(value)
        value = Dense(256)(value, kernel_initializer="random_uniform", 
                                  bias_initializer="random_uniform") # Linear layer.
        value = Activation("relu")(value)

        # Final value layer. Outputs probability of win/loss/draw as value between -1 and 1.
        value = Dense(1)(value, kernel_initializer="random_uniform", 
                                bias_initializer="random_uniform")
        value = Activation("tanh")(value)

        self.model = Model(inputs=inp, outputs=[policy, value])
        self.model.compile(optimizer=SGD(lr=constants.LEARNING_RATE,
                                    decay=constants.WEIGHT_DECAY,
                                    momentum=constants.MOMENTUM),
                                    loss='mean_squared_error')

        plot_model(self.model, to_file='../resources/model_graph.png', show_shapes=True)

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
    
    def update_weights(self, inputs, expected_out, weight_decay):
        """
        Train the network on a batch of data.
        @param inputs - Numpy array of game 'images', i.e: game states.
        @param expected_out - Numpy array of tuples with (terminal values
        of inputted states, action/move probability distribution of inputted states).
        @param weight_decay - Weight decay from constants.
        """
        result = self.model.train_on_batch(inputs, expected_out)
