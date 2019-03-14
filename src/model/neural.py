"""
-------------------------------
neural: Neural Network wrapper.
-------------------------------
"""
from threading import Lock
from os import getpid
from tensorflow import Session, ConfigProto, reset_default_graph, get_default_graph
from keras.backend.tensorflow_backend import set_session, clear_session
from keras.backend import get_session
from keras.layers import Dense, Conv2D, BatchNormalization, Input, Flatten
from keras.layers.core import Activation
from keras.optimizers import SGD
from keras.models import Sequential
from keras.models import save_model, Model
from keras.utils.vis_utils import plot_model
import numpy as np
from model.residual import Residual
import constants

class NeuralNetwork:
    """
    The dual policy network, which guides,
    and is trained by, the MCTS algorithm.
    """
    def __init__(self, game, model=None):
        self.game = game
        if model:
            self.model = model
            return
        # Clean up from previous TF graphs.
        reset_default_graph()
        clear_session()

        # Config options, to stop TF from eating all GPU memory.
        config = ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = constants.MAX_GPU_FRACTION
        config.gpu_options.allow_growth = True
        #config.gpu_options.visible_device_list = "0"
        set_session(Session(config=config))

        inp = self.input_layer(game)

        # -=-=-=-=-=- Network 'body'. -=-=-=-=-=-
        # First convolutional layer.
        out = Conv2D(constants.CONV_FILTERS, kernel_size=3, strides=1, padding="same",
                     kernel_initializer="random_uniform",
                     bias_initializer="random_uniform")(inp)
        out = BatchNormalization()(out)
        out = Activation("relu")(out)

        # Residual layers, 19 in total.
        for _ in range(constants.RES_LAYERS):
            out = Residual(constants.CONV_FILTERS, constants.CONV_FILTERS, out)

        # -=-=-=-=-=- Policy 'head'. -=-=-=-=-=-
        policy = Conv2D(2, kernel_size=1, strides=1, padding="same",
                        kernel_initializer="random_uniform",
                        bias_initializer="random_uniform")(out)
        policy = BatchNormalization()(policy)
        policy = Activation("relu")(policy)

        outputs = self.policy_layers(game, policy)

        # -=-=-=-=-=- Value 'head'. -=-=-=-=-=-
        value = Conv2D(1, kernel_size=1, strides=1, kernel_initializer="random_uniform",
                       bias_initializer="random_uniform")(out)
        value = BatchNormalization()(value)
        value = Activation("relu")(value)

        value = Flatten()(value)
        value = Dense(constants.CONV_FILTERS, kernel_initializer="random_uniform",
                      bias_initializer="random_uniform")(value) # Linear layer.
        value = Activation("relu")(value)

        # Final value layer. Outputs probability of win/loss/draw as value between -1 and 1.
        value = Dense(1, kernel_initializer="random_uniform",
                      bias_initializer="random_uniform")(value)
        value = Activation("tanh")(value)

        outputs.append(value)

        self.model = Model(inputs=inp, outputs=outputs)
        self.model.compile(optimizer=SGD(lr=constants.LEARNING_RATE,
                                         decay=constants.WEIGHT_DECAY,
                                         momentum=constants.MOMENTUM),
                           loss='mean_squared_error')
        self.model._make_predict_function()

    def input_layer(self, game):
        game_type = type(game).__name__
        input_depth = 1
        if game_type == "Latrunculi":
            input_depth = 4
        elif game_type == "Connect_Four":
            input_depth = 2
        self.input_stacks = input_depth
        return Input((game.size, game.size, input_depth))

    def policy_layers(self, game, prev):
        game_type = type(game).__name__
        if game_type == "Latrunculi":
            # Split into...
            # ...move policies.
            policy_moves = Conv2D(4, kernel_size=3, strides=1, padding="same",
                                  kernel_initializer="random_uniform",
                                  bias_initializer="random_uniform")(prev)
            policy_moves = BatchNormalization()(policy_moves)

            # ...delete captured pieces policy.
            policy_delete = Conv2D(1, kernel_size=3, strides=1, padding="same",
                                   kernel_initializer="random_uniform",
                                   bias_initializer="random_uniform")(prev)
            return [policy_moves, policy_delete]
        if game_type == "Connect_Four":
            # Vector of probabilities for all squares.
            policy = Flatten()(prev)
            policy = Dense(game.size*game.size,
                           kernel_initializer="random_uniform",
                           bias_initializer="random_uniform")(policy)
            return [policy]
        return []

    def save_as_image(self):
        plot_model(self.model, to_file='../resources/model_graph.png', show_shapes=True)

    def evaluate(self, inp):
        """
        Evaluate a given state 'image' using the network.
        @param inp - Image/structured data for a state.
        @returns (p, z)
        - p: A 4D array of probabilities for each
        available action in state. These values help
        guide the MCTS search.
        - z: A value indicating the expected outcome of
        the game from the given state.
        """
        if len(inp.shape) < 4:
            size = self.game.size
            inp = np.array([inp]).reshape((-1, size, size, self.input_stacks))
        output = self.model.predict(inp)
        game_type = type(self.game).__name__

        policy_moves = output[0][:]
        policy_moves -= np.min(policy_moves)
        policy_moves /= np.ptp(policy_moves)

        if game_type == "Latrunculi":
            policy_delete = output[1][:]
            policy_delete -= np.min(policy_delete)
            peaks = np.ptp(policy_delete)
            if peaks:
                policy_delete /= peaks

            return ((policy_moves, policy_delete), output[2][:])
        return policy_moves, output[1][:]

    def train(self, inputs, expected_out):
        """
        Train the network on a batch of data.
        @param inputs - Numpy array of game 'images', i.e: game states.
        @param expected_out - Numpy array of tuples with (terminal values
        of inputted states, action/move probability distribution of inputted states).
        """
        result = self.model.train_on_batch(inputs, expected_out)
        return result

class DummyNetwork(NeuralNetwork):
    """
    The dummy network is used at the start
    of training, to save on performance.
    It simply returns random policies and value.
    """
    def __init__(self, board_size, action_space=4):
        NeuralNetwork.__init__(self, board_size, action_space)

    def evaluate(self, inp):
        shape = inp.shape
        policy_moves = np.random.uniform(0, 1, (shape[0], shape[1], self.action_space))
        policy_remove = np.random.uniform(0, 1, (shape[0], shape[1], 1))
        return (policy_moves, policy_remove), np.random.uniform()
