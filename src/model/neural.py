"""
-----------------------------
neural: Neural Network stuff.
-----------------------------
"""
from multiprocessing import Lock, Process
from tensorflow import Session, ConfigProto, reset_default_graph, get_default_graph
from keras.backend.tensorflow_backend import set_session, clear_session
from keras.backend import get_session
from keras.layers import Dense, Conv2D, BatchNormalization, Input, Flatten
from keras.layers.core import Activation
from keras.optimizers import SGD
from keras.models import Sequential
from keras.models import save_model, Model
from keras.utils.vis_utils import plot_model
from model.residual import Residual
import numpy as np
import constants

class NeuralNetwork:
    """
    The dual policy network, which guides,
    and is trained by, the MCTS algorithm.
    """
    def __init__(self, board_size, action_space=4, train_immediately=True):
        self.action_space = action_space
        self.board_size = board_size
        print("CREATING NETWORK")
        #self.lock = Lock()
        if not train_immediately:
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

        session = get_session()
        nn_graph = get_default_graph()

        inp = Input((board_size, board_size, 4))

        # -=-=-=-=-=- Network 'body'. -=-=-=-=-=-
        # First convolutional layer.
        out = Conv2D(256, kernel_size=3, strides=1, padding="same",
                        kernel_initializer="random_uniform",
                        bias_initializer="random_uniform")(inp)
        out = BatchNormalization()(out)
        out = Activation("relu")(out)

        # Residual layers, 19 in total.
        for _ in range(19):
            out = Residual(256, 256, out)

        # -=-=-=-=-=- Policy 'head'. -=-=-=-=-=-
        policy = Conv2D(2, kernel_size=1, strides=1, padding="same",
                        kernel_initializer="random_uniform",
                        bias_initializer="random_uniform")(out)
        policy = BatchNormalization()(policy)
        policy = Activation("relu")(policy)

        # Split into...
        # ...move policies.
        policy_moves = Conv2D(action_space, kernel_size=3, strides=1, padding="same",
                                kernel_initializer="random_uniform",
                                bias_initializer="random_uniform")(policy)
        policy_moves = BatchNormalization()(policy_moves)

        # ...delete captured pieces policy.
        policy_delete = Conv2D(1, kernel_size=3, strides=1, padding="same",
                                kernel_initializer="random_uniform",
                                bias_initializer="random_uniform")(policy)

        # -=-=-=-=-=- Value 'head'. -=-=-=-=-=-
        value = Conv2D(1, kernel_size=1, strides=1, kernel_initializer="random_uniform",
                        bias_initializer="random_uniform")(out)
        value = BatchNormalization()(value)
        value = Activation("relu")(value)

        value = Flatten()(value)
        value = Dense(256, kernel_initializer="random_uniform",
                        bias_initializer="random_uniform")(value) # Linear layer.
        value = Activation("relu")(value)

        # Final value layer. Outputs probability of win/loss/draw as value between -1 and 1.
        value = Dense(1, kernel_initializer="random_uniform",
                        bias_initializer="random_uniform")(value)
        value = Activation("tanh")(value)

        self.model = Model(inputs=inp, outputs=[policy_moves, policy_delete, value])
        self.model.compile(optimizer=SGD(lr=constants.LEARNING_RATE,
                                            decay=constants.WEIGHT_DECAY,
                                            momentum=constants.MOMENTUM),
                            loss='mean_squared_error')
        self.model._make_predict_function()

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
        print("Eval on {}".format(Process.pid))
        #self.lock.acquire()
        if len(inp.shape) < 4:
            inp = np.array([inp]).reshape((-1, 4, 4, 4))
        output = self.model.predict(inp)
        #self.lock.release()

        policy_moves = output[0][0]
        policy_moves -= np.min(policy_moves)
        policy_moves /= np.ptp(policy_moves)

        policy_delete = output[1][0]
        policy_delete -= np.min(policy_delete)
        peaks = np.ptp(policy_delete)
        if peaks:
            policy_delete /= peaks

        return ((policy_moves, policy_delete), output[2][0][0])

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
