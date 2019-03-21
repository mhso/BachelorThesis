"""
-------------------------------
neural: Neural Network wrapper.
-------------------------------
"""
import numpy as np
from tensorflow import Session, ConfigProto, reset_default_graph
from keras import losses
from keras.backend.tensorflow_backend import set_session, clear_session
from keras.layers import Dense, Conv2D, BatchNormalization, Input, Flatten
from keras.layers.core import Activation
from keras.optimizers import SGD
from keras.models import Model
from keras.initializers import random_uniform, random_normal
from keras.utils.vis_utils import plot_model
from model.residual import Residual
from config import Config

class NeuralNetwork:
    """
    The dual policy network, which guides,
    and is trained by, the MCTS algorithm.
    """
    def __init__(self, game, model=None):
        self.game = game
        if model:
            self.model = model
            if not self.model._is_compiled:
                self.compile_model(self.model, game)
            return
        # Clean up from previous TF graphs.
        reset_default_graph()
        clear_session()

        # Config options, to stop TF from eating all GPU memory.
        nn_config = ConfigProto()
        nn_config.gpu_options.per_process_gpu_memory_fraction = Config.MAX_GPU_FRACTION
        nn_config.gpu_options.allow_growth = True
        #Config.gpu_options.visible_device_list = "0"
        set_session(Session(config=nn_config))

        inp = self.input_layer(game)

        # -=-=-=-=-=- Network 'body'. -=-=-=-=-=-
        # First convolutional layer.
        out = Conv2D(Config.CONV_FILTERS, kernel_size=3, strides=1, padding="same",
                     kernel_initializer=self.get_initializer(0, 1, Config.BATCH_SIZE),
                     use_bias=Config.USE_BIAS)(inp)
        out = BatchNormalization()(out)
        out = Activation("relu")(out)

        # Residual layers, 19 in total.
        for _ in range(Config.RES_LAYERS):
            out = Residual(Config.CONV_FILTERS, Config.CONV_FILTERS, out)

        # -=-=-=-=-=- Policy 'head'. -=-=-=-=-=-
        policy = Conv2D(2, kernel_size=1, strides=1, padding="same", use_bias=Config.USE_BIAS)(out)
        policy = BatchNormalization()(policy)
        policy = Activation("relu")(policy)

        outputs = self.policy_layers(game, policy)

        # -=-=-=-=-=- Value 'head'. -=-=-=-=-=-
        value = Conv2D(1, kernel_size=1, strides=1, use_bias=Config.USE_BIAS)(out)
        value = BatchNormalization()(value)
        value = Activation("relu")(value)

        value = Flatten()(value)
        value = Dense(Config.CONV_FILTERS, use_bias=Config.USE_BIAS)(value) # Linear layer.
        value = Activation("relu")(value)

        # Final value layer. Outputs probability of win/loss/draw as value between -1 and 1.
        value = Dense(1, kernel_initializer=self.get_initializer(-1, 1, Config.CONV_FILTERS),
                      use_bias=Config.USE_BIAS)(value)
        value = Activation("tanh")(value)

        outputs.append(value)

        self.model = Model(inputs=inp, outputs=outputs)
        self.compile_model(self.model, game)
        self.model._make_predict_function()

    def get_initializer(self, min_val, max_val, inputs=10):
        if Config.WEIGHT_INITIALIZER == "uniform":
            return random_uniform(min_val, max_val)
        if Config.WEIGHT_INITIALIZER == "normal":
            return random_normal(min_val, 1/np.sqrt(inputs)) # Stddev = 1/sqrt(inputs)

    def compile_model(self, model, game):
        game_name = type(game).__name__
        loss_funcs = [losses.binary_crossentropy]
        if game_name == "Latrunculi":
            loss_funcs.append(losses.binary_crossentropy)
        loss_funcs.append(losses.mean_squared_error)
        model.compile(optimizer=SGD(lr=Config.LEARNING_RATE,
                                    decay=Config.WEIGHT_DECAY,
                                    momentum=Config.MOMENTUM),
                      loss=loss_funcs,
                      metrics=["accuracy"])

    #softmax_cross_entropy_with_logits_v2
    def input_layer(self, game):
        game_type = type(game).__name__
        input_depth = 1
        if game_type == "Latrunculi":
            input_depth = 4
        else:
            input_depth = 2
        self.input_stacks = input_depth
        return Input((input_depth, game.size, game.size))

    def policy_layers(self, game, prev):
        game_type = type(game).__name__
        if game_type == "Latrunculi":
            # Split into...
            # ...move policies.
            policy_moves = Conv2D(4, kernel_size=3, strides=1, padding="same", use_bias=Config.USE_BIAS)(prev)
            policy_moves = BatchNormalization()(policy_moves)

            # ...delete captured pieces policy.
            policy_delete = Conv2D(1, kernel_size=3, strides=1, padding="same", use_bias=Config.USE_BIAS)(prev)
            return [policy_moves, policy_delete]
        else:
            # Vector of probabilities for all squares.
            policy = Flatten()(prev)
            policy = Dense(game.size*game.size,
                           kernel_initializer=self.get_initializer(0, 1, Config.CONV_FILTERS * Config.BATCH_SIZE),
                           use_bias=Config.USE_BIAS)(policy)
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
            inp = np.array([inp]).reshape((-1, self.input_stacks, size, size))
        output = self.model.predict(inp)
        game_type = type(self.game).__name__

        policy_moves = output[0][:]
        policy_moves -= np.min(policy_moves)
        peaks = np.ptp(policy_moves)
        policy_moves /= peaks

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
