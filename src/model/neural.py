"""
-------------------------------
neural: Neural Network wrapper.
-------------------------------
"""
import numpy as np
import tensorflow as tf
from keras import losses
from keras.backend.tensorflow_backend import set_session, clear_session, get_session
from keras.layers import Dense, Conv2D, BatchNormalization, Input, Flatten
from keras.layers.core import Activation
from keras.optimizers import SGD
from keras.models import Model, clone_model
from keras.initializers import random_uniform, random_normal
from keras.regularizers import l2
from keras.utils import get_custom_objects
from keras.utils.vis_utils import plot_model
from keras.layers import LeakyReLU
from model.residual import Residual
from config import Config

def softmax_cross_entropy_with_logits(y_bool, y_pred):
    zeros = tf.zeros(shape=(tf.shape(y_bool)), dtype=tf.float32)
    where_true = tf.equal(y_bool, zeros)

    where_false = tf.fill(tf.shape(y_bool), -100.0)
    pred = tf.where(where_true, where_false, y_pred)
    return tf.nn.softmax_cross_entropy_with_logits_v2(labels=y_bool, logits=pred)

def set_nn_config():
    # Clean up from previous TF graphs.    
    tf.reset_default_graph()
    clear_session()

    get_custom_objects().update({"softmax_cross_entropy_with_logits": softmax_cross_entropy_with_logits})

    # Config options, to stop TF from eating all GPU memory.
    nn_config = tf.ConfigProto()
    nn_config.gpu_options.per_process_gpu_memory_fraction = Config.MAX_GPU_FRACTION
    nn_config.gpu_options.allow_growth = True
    set_session(tf.Session(config=nn_config))

class NeuralNetwork:
    """
    The dual policy network, which guides,
    and is trained by, the MCTS algorithm.
    """
    input_stacks = 0

    def __init__(self, game, model=None):
        self.game = game
        if model:
            self.input_layer(game)
            self.model = model
            self.model._make_predict_function()
            if not self.model._is_compiled:
                self.compile_model(self.model, game)
            return

        set_nn_config()

        inp = self.input_layer(game)

        # -=-=-=-=-=- Network 'body'. -=-=-=-=-=-
        # First convolutional layer.
        out = self.conv_layer(inp, Config.CONV_FILTERS, 3)

        # Residual layers.
        for _ in range(Config.RES_LAYERS):
            out = Residual(Config.CONV_FILTERS, Config.CONV_FILTERS, out)

        # -=-=-=-=-=- Policy 'head'. -=-=-=-=-=-
        policy = self.policy_head(game, out)

        # -=-=-=-=-=- Value 'head'. -=-=-=-=-=-
        value = self.value_head(out)

        self.model = Model(inputs=inp, outputs=[policy, value])
        self.compile_model(self.model, game)
        self.model._make_predict_function()

    def conv_layer(self, inp, filters, kernel_size):
        """
        Construct a 2D convolutional, rectified, batchnormalized
        layer with the given input, filters and kernel size.
        """
        out = Conv2D(filters, kernel_size=(kernel_size, kernel_size), strides=1, padding="same",
                     use_bias=Config.USE_BIAS,
                     kernel_regularizer=l2(Config.REGULARIZER_CONST))(inp)
        out = BatchNormalization()(out)
        out = LeakyReLU()(out)
        return out

    def get_initializer(self, min_val, max_val, inputs=10):
        if Config.WEIGHT_INITIALIZER == "uniform":
            return random_uniform(min_val, max_val)
        if Config.WEIGHT_INITIALIZER == "normal":
            return random_normal(min_val, 1/np.sqrt(inputs)) # Stddev = 1/sqrt(inputs)

    def compile_model(self, model, game):
        """
        Create relevant loss functions, weights and
        optimizer, and compile the neural network model.
        """
        game_name = type(game).__name__
        # Policy head loss weights & loss function.
        loss_weights = [0.5, 0.5]
        loss_funcs = [softmax_cross_entropy_with_logits]
        if game_name == "Latrunculi":
            loss_funcs.append(losses.binary_crossentropy)
        # Value head loss weights & loss function.
        loss_funcs.append(losses.mean_squared_error)

        # Stochastic Gradient Descent optimizer with momentum.
        model.compile(optimizer=SGD(lr=Config.LEARNING_RATE,
                                    decay=Config.WEIGHT_DECAY,
                                    momentum=Config.MOMENTUM),
                      loss_weights=loss_weights,
                      loss=loss_funcs,
                      metrics=[softmax_cross_entropy_with_logits, "accuracy"])

    def input_layer(self, game):
        game_type = type(game).__name__
        input_depth = 1
        if game_type == "Latrunculi":
            input_depth = 4
        else:
            input_depth = 2
        self.input_stacks = input_depth
        return Input((input_depth, game.size, game.size))

    def policy_head(self, game, prev):
        policy = self.conv_layer(prev, 2, 1)
        game_type = type(game).__name__
        if game_type == "Latrunculi":
            # Split into...
            # ...move policies.
            policy_moves = Conv2D(4, kernel_size=3, strides=1, padding="same",
                                  use_bias=Config.USE_BIAS, name="policy_head")

            # ...delete captured pieces policy.
            policy_delete = Conv2D(1, kernel_size=3, strides=1, padding="same",
                                   use_bias=Config.USE_BIAS, name="policy_head2")(policy)
            return policy_moves
        else:
            # Vector of probabilities for all squares.
            policy = Flatten()(policy)
            policy = Dense(game.size*game.size,
                           kernel_regularizer=l2(Config.REGULARIZER_CONST),
                           use_bias=Config.USE_BIAS, name="policy_head")(policy)
        return policy

    def value_head(self, prev):
        value = self.conv_layer(prev, 1, 1)

        # Flatten into linear layer.
        value = Flatten()(value)
        value = Dense(Config.CONV_FILTERS, use_bias=Config.USE_BIAS,
                      kernel_regularizer=l2(Config.REGULARIZER_CONST))(value)
        value = LeakyReLU()(value)

        # Final value layer. Linar layer with one output neuron.
        value = Dense(1,
                      kernel_regularizer=l2(Config.REGULARIZER_CONST),
                      use_bias=Config.USE_BIAS)(value)
        # Tanh activation, outputs probability of win/loss/draw as scalar value between -1 and 1.
        value = Activation("tanh", name="value_head")(value)
        return value

    def save_as_image(self):
        plot_model(self.model, to_file='../resources/model_graph.png', show_shapes=True)

    def shape_input(self, inp):
        reshaped = inp
        if len(inp.shape) < 4:
            size = self.game.size
            reshaped = np.array([inp]).reshape((-1, self.input_stacks, size, size))
        return reshaped

    def copy_model(self, game):
        model_copy = clone_model(self.model)
        model_copy.build(self.input_layer(game))
        self.compile_model(model_copy, game)
        model_copy.set_weights(self.model.get_weights())
        return model_copy

    def log_flops(self):
        """
        Function for testing FLOPS (Floating Operations Per Second)
        for a specific network model.
        Curtesy of: https://stackoverflow.com/a/47561171
        """
        run_meta = tf.RunMetadata()
        opts = tf.profiler.ProfileOptionBuilder.float_operation()    
        flops = tf.profiler.profile(get_session().graph, run_meta=run_meta, cmd='op', options=opts)

        opts = tf.profiler.ProfileOptionBuilder.trainable_variables_parameter()    
        params = tf.profiler.profile(get_session().graph, run_meta=run_meta, cmd='op', options=opts)

        if flops is not None:
            with open("../resources/flops_summary.txt", "w") as file:
                file.write("FLOPS SUMMARY:\n")
                file.write(str(flops.total_float_ops)+" FLOPS\n")
                file.write(str(params.total_parameters) + " params.")

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
        shaped_input = self.shape_input(inp)
        output = self.model.predict(shaped_input)
        game_type = type(self.game).__name__

        policy_moves = output[0][:]

        if False:
            self.log_flops()

        if game_type == "Latrunculi":
            policy_delete = output[1][:]

            return ((policy_moves, policy_delete), output[2][:])
        return policy_moves, output[1][:]

    def train(self, inputs, expected_out):
        """
        Train the network on a batch of data.
        @param inputs - Numpy array of game 'images', i.e: game states.
        @param expected_out - Numpy array of tuples with (terminal values
        of inputted states, action/move probability distribution of inputted states).
        """
        result = self.model.fit(inputs, expected_out, batch_size=Config.BATCH_SIZE, verbose=0,
                                epochs=Config.EPOCHS_PER_BATCH, validation_split=Config.VALIDATION_SPLIT)
        return result.history
