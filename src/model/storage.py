"""
storage: Stores/saves/loads neural network models for use in
training and self-play, as well as replay buffers generated from self-play.
"""
import numpy as np
import constants
import pickle
#import io
#from io import BytesIO
import os
from model.neural import NeuralNetwork, DummyNetwork
from glob import glob
from keras.models import save_model, load_model
from util.sqlUtil import SqlUtil
from util.timerUtil import TimerUtil

class ReplayStorage:
    """
    This class manages the saving/loading of replays from games.
    """
    def __init__(self):
        self.max_games = constants.MAX_GAME_STORAGE
        self.batch_size = constants.BATCH_SIZE
        self.buffer = []

    def save_game(self, game):
        if len(self.buffer) >= self.max_games:
            self.buffer.pop(0) # Remove oldest game.
        self.buffer.append(game)

    def sample_batch(self):
        """
        Draw a set amount of random samples from the saved games.
        @returns - A tuple of two arrays, one with input data for
        the neural network and one with a corresponding list of
        expected outcomes of the game + move probability distribution.
        """
        # Sum up how many moves were made during all games in the buffer.
        move_sum = float(sum(len(g.history) for g in self.buffer))
        # Draw random games, with each game weighed according to the amount
        # of moves made in that game.
        batch = np.random.choice(
            self.buffer,
            size=self.batch_size,
            p=[len(g.history)/move_sum for g in self.buffer]
        )
        # Draw random state index values from all chosen games.
        state_indices = [(g, np.random.randint(0, len(g.history))) for g in batch]
        images = []
        out1 = []
        out2 = []
        out3 = []
        # Create input/expected output data for neural network training.
        for game, index in state_indices:
            images.append(game.structure_data(game.history[index]))
            target_value, policies = game.make_target(index)
            target_policy_moves, target_policy_remove = game.map_actions(policies)
            out1.append(target_policy_moves)
            out2.append(target_policy_remove)
            out3.append(target_value)
        return np.array(images), [np.array(out1), np.array(out2), np.array(out3)]

    def full_buffer(self):
        return len(self.buffer) == constants.BATCH_SIZE

    def save_replay(self, game, step):
        """
        serializes a game, and saves it to a file,
        under the correct neural network version,
        given by the step parameter.
        """
        folder_name = "../resources/replays/"
        version_nn = str(step)
        folder_nn = "NNv" + version_nn + "/"
        file_name = "game"
        file_extension = ".bin"

        number_of_files = (glob(folder_name + folder_nn + "*" + file_extension)).__len__()
        game_number = number_of_files+1

        if not os.path.exists((folder_name + folder_nn)):
            os.makedirs((folder_name + folder_nn))

        try:
            new_file = open((folder_name + folder_nn + file_name + str(game_number) + file_extension), "xb")
            pickle.dump(game, new_file)
            new_file.close()
            print("game was saved to file")
        except IOError:
            print("something went wrong, when trying to save a replay")

    def load_replay(self, step):
        """
        method for loading saved games back into Replay Storage buffer.
        The method selects the newest NN version, where the amount of saved games
        is less than the constant MAX_GAME_STORAGE,
        it then loads the games directly into the buffer.
        The "step" parameter, defines the newest NN version we are interested in.
        """
        folder_name = "../resources/replays/"
        folder_nn_no_version = "NNv"
        file_extension = ".bin"

        try:
            if step is None:
                current_step = len(glob(folder_name))-1
            else:
                current_step = step

            step_counter = current_step
            file_counter = 0
            while step_counter >= 0 and file_counter < constants.MAX_GAME_STORAGE:
                file_list = glob(folder_name + folder_nn_no_version + str(step_counter) + "/" + "*" + file_extension)

                for f in file_list:
                    if file_counter < constants.MAX_GAME_STORAGE:
                        open_file = open(f, "rb")
                        game = pickle.load(open_file)
                        self.buffer.append(game)
                        file_counter += 1
                        open_file.close()
                    else:
                        break
                step_counter -= 1
            print("Saved games were loaded from files")
        except IOError:
            print("something went wrong when trying to load games into buffer")


    def save_game_to_sql(self, game):
        filename = "game"

        data = pickle.dumps(game)
        sql_conn = SqlUtil.connect()
        SqlUtil.game_data_insert_row(sql_conn, TimerUtil.get_computer_hostname(), filename, "sql blob testing",  data)
        print("Game inserted into sql database table")

    def load_game_from_sql(self):
        sql_conn = SqlUtil.connect()
        games = SqlUtil.game_data_select_newest_games(sql_conn) #games from sql, arranged as an array of tuples, each tuple containing (bin_data,(nothing for some reason))

        for g in games:
            game = g[0]
            self.buffer.append(game)

        print("Games selected from sql database table, and inserted into replay_buffer")


    def __str__(self):
        return "<ReplayStorage: {} games, total length of games: {}>".format(len(self.buffer), sum(len(g.history) for g in self.buffer))

class NetworkStorage:
    """
    This class manages the saving/loading of neural networks.
    The network periodically saves it's model to this class and
    MCTS loads the newest network during self-play.
    """
    def __init__(self):
        self.networks = {}
        self.curr_step = 0

    def latest_network(self):
        return self.networks[self.curr_step]

    def save_network(self, step, network):
        self.networks[step] = network
        if len(self.networks) > constants.MAX_NETWORK_STORAGE:
            new_dict = dict()
            for i, k in self.networks:
                if i > 0:
                    new_dict[k] = self.networks[k]
            self.networks = new_dict
        self.curr_step = step

    def replace_dummy_network(self):
        old_network = self.latest_network()
        network = NeuralNetwork(old_network.board_size, old_network.action_space, False)
        self.save_network(self.curr_step, network)

    def save_network_to_file(self, step, network):
        """
        serializes the Neural Network, and saves it to a file,
        under the correct version, given by the step parameter
        """
        folder_name = "../resources/networks/"
        version_nn = str(step)
        file_name = "network"

        if not os.path.exists((folder_name)):
            os.makedirs((folder_name))
        try:
            save_model(network.model, (folder_name + file_name + str(version_nn)), True, True)
            print("Neural Network was saved to file")
        except IOError:
            print("saving the network failed")

    def load_network_from_file(self, step):
        """
        Deserializes the Neural Network,
        and loads it from a file, based on the given step number.
        This network is then returned.
        """
        folder_name = "../resources/networks/"
        file_name = "network"

        try:
            if step is None:
                current_step = len(glob(folder_name + "*"))-1
                self.curr_step = current_step
            else:
                current_step = step
            version_nn = str(current_step)

            network = load_model(folder_name + file_name + str(version_nn), None, True)
            print("Neural Network was loaded from file")
            return network
        except IOError:
            if not os.path.exists((folder_name + file_name + str(version_nn))):
                print("network file was not found: " + folder_name + file_name + str(version_nn))
            else:
                print("file was found, but something else went wrong")

    def save_network_to_sql(self, network):
        data = pickle.dumps(network) #TODO: change this to appropriate method
        sql_conn = SqlUtil.connect()
        SqlUtil.game_data_insert_row(sql_conn, TimerUtil.get_computer_hostname(), filename, "sql blob testing",  data)
        print("Game inserted into sql database table")

    def load_newest_network_from_sql(self):
        sql_conn = SqlUtil.connect()
        network = SqlUtil.game_data_select_filename(sql_conn, filename) #TODO: change this to appropriate method
        unpickled_game = pickle.loads(network)
        print("Game selected from sql database table")
        return unpickled_game
