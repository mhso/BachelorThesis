"""
storage: Stores/saves/loads neural network models for use in
training and self-play, as well as replay buffers generated from self-play.
"""
from glob import glob
import pickle
import os
import numpy as np
from keras.models import save_model, load_model, Model
from model.neural import set_nn_config
from config import Config
from util.sqlUtil import SqlUtil
from util.timerUtil import TimerUtil

class ReplayStorage:
    """
    This class manages the saving/loading of replays from games.
    """
    def __init__(self):
        self.buffer = []

    def save_game(self, game):
        if len(self.buffer) >= Config.MAX_GAME_STORAGE:
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
            size=Config.BATCH_SIZE,
            p=[len(g.history)/move_sum for g in self.buffer]
        )
        # Draw random state index values from all chosen games.
        state_indices = [(g, np.random.randint(0, len(g.history))) for g in batch]
        images = []
        expected_outputs = [[], [], []] if type(self.buffer[0]).__name__ == "Latrunculi" else [[], []]
        # Create input/expected output data for neural network training.
        for game, index in state_indices:
            images.append(game.structure_data(game.history[index]))
            target_value, policies = game.make_target(index)
            target_policies = game.map_visits(policies)
            """
            print(f"State at index {index}:\n{game.history[index]}")
            winner = "White" if game.terminal_value == 1 else "Black" if game.terminal_value != 0 else "Draw"
            print(f"Last state:\n{game.history[-1]}")
            print(f"Winner: {winner}")
            print(f"Policies:\n{policies}")
            print(f"Target policies:\n{target_policies}")
            print(f"Value type of game: {game.val_type}")
            print(f"Terminal value: {game.terminal_value}")
            print(f"Q-value: {game.q_value_history[index]}")
            print(f"Target value: {target_value}")
            print(f"===============================================")
            """
            for i in range(len(target_policies)):
                expected_outputs[i].append(target_policies[i])
            expected_outputs[-1].append(target_value)

        expected_outputs = [np.array(arr, dtype="float32") for arr in expected_outputs]
        return np.array(images, dtype="float32"), expected_outputs

    def full_buffer(self):
        return len(self.buffer) == Config.BATCH_SIZE

    def save_replay(self, game, step, game_type):
        """
        serializes a game, and saves it to a file,
        under the correct neural network version,
        given by the step parameter.
        """
        folder_name = "../resources/"
        data_type = "/replays/"
        version_nn = str(step)
        folder_nn = "NNv" + version_nn + "/"
        file_name = "game"
        file_extension = ".bin"

        number_of_files = (glob(folder_name + game_type + data_type + folder_nn + "*" + file_extension)).__len__()
        game_number = number_of_files+1

        if not os.path.exists((folder_name + game_type + data_type + folder_nn)):
            os.makedirs((folder_name + game_type + data_type + folder_nn))

        try:
            new_file = open((folder_name + game_type + data_type + folder_nn + file_name + str(game_number) + file_extension), "xb")
            pickle.dump(game, new_file)
            new_file.close()
            print("game was saved to file")
        except IOError:
            print("something went wrong, when trying to save a replay")

    def load_replay(self, step, game_type):
        """
        method for loading saved games back into Replay Storage buffer.
        The method selects the newest NN version, where the amount of saved games
        is less than the constant MAX_GAME_STORAGE,
        it then loads the games directly into the buffer.
        The "step" parameter, defines the newest NN version we are interested in.
        """
        folder_name = "../resources/"
        data_type = "/replays/"
        folder_nn_no_version = "NNv"
        file_extension = ".bin"

        try:
            folders = glob(folder_name + game_type + data_type + folder_nn_no_version + "*")
            folders.sort(key=lambda s: int(s.split("NNv")[-1]))
            if step is None:
                current_step = len(folders)-1
            else:
                current_step = step

            step_counter = current_step
            file_counter = 0
            while step_counter >= 0 and file_counter < Config.MAX_GAME_STORAGE:
                file_list = glob(folders[step_counter] + "/" + "*" + file_extension)

                for f in file_list:
                    if file_counter < Config.MAX_GAME_STORAGE:
                        open_file = open(f, "rb")
                        game = pickle.load(open_file)
                        self.buffer.append(game)
                        file_counter += 1
                        open_file.close()
                    else:
                        break
                step_counter -= 1
            print(f"{file_counter} saved games were loaded from files")
        except IOError:
            print("something went wrong when trying to load games into buffer")


    def save_game_to_sql(self, game):
        filename = "game"

        data = pickle.dumps(game)
        sql_conn = SqlUtil.connect()
        SqlUtil.game_data_insert_row(sql_conn, TimerUtil.get_computer_hostname(), filename, "sql blob testing",  data)
        print("Game inserted into sql database table")

    def load_games_from_sql(self):
        sql_conn = SqlUtil.connect()
        games = SqlUtil.game_data_select_newest_games(sql_conn) #games from sql, arranged as an array of tuples, each tuple containing (bin_data,(nothing for some reason))

        for g in games:
            game = g[0]
            if game is not None:
                unpickledGame = pickle.loads(game)
                self.buffer.append(unpickledGame)

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

    def get_network(self, step):
        network_id = step if step != -1 else self.curr_step
        return self.networks[network_id]

    def save_network(self, step, network):
        self.networks[step] = network
        if len(self.networks) > Config.MAX_NETWORK_STORAGE:
            # Don't remove latest macro network.
            macro = round(self.curr_step, -2)
            macro = macro if macro <= self.curr_step else macro - Config.SAVE_CHECKPOINT_MACRO
            prev_macro = macro - Config.SAVE_CHECKPOINT_MACRO
            if macro == 0:
                macro = -1
            if prev_macro == 0:
                prev_macro = -1
            # Find step of oldest nework, apart from the macro network.
            lowest_step = self.curr_step
            for s in self.networks:
                if s < lowest_step and s != macro and s != prev_macro:
                    lowest_step = s
            # Copy all networks, but the oldest.
            new_dict = dict()
            for s, n in self.networks.items():
                if s != lowest_step:
                    new_dict[s] = n
            self.networks = new_dict
        self.curr_step = step

    def save_network_to_file(self, step, network, game_type):
        """
        serializes the Neural Network, and saves it to a file,
        under the correct version, given by the step parameter
        """
        folder_name = "../resources/"
        data_type = "/networks/"
        data_type2 = "/macroNetworks/"
        version_nn = str(step)
        file_name = "network"

        if not os.path.exists((folder_name + game_type + data_type)):
            os.makedirs((folder_name + game_type + data_type))
        if not os.path.exists((folder_name + game_type + data_type2)):
            os.makedirs((folder_name + game_type + data_type2))

        try:
            #save the network as a file
            save_model(network.model, (folder_name + game_type + data_type + file_name + str(version_nn)), True, True)
            print("Neural Network was saved to file")
            file_list = glob(folder_name + game_type + data_type + "*")

            #save macro network
            if (step % Config.SAVE_CHECKPOINT_MACRO) == 0:
                save_model(network.model, (folder_name + game_type + data_type2 + file_name + str(version_nn)), True, True)
                print("Neural Network was saved to file in the macroNetworks folder")
            
            #delete files, so we only save the 10 newest NN's
            step_to_remove = step - Config.MAX_NETWORK_STORAGE
            #the +1 int he first condition of the loop, is in order to prevent the loop from running n times, every time.
            while len(file_list) > (Config.MAX_NETWORK_STORAGE + 1) and step_to_remove >= 0: 
                s = str(step_to_remove)
                os.remove(folder_name + game_type + data_type + file_name + s)
                step_to_remove -= 1
                print("old network was deleted")

        except IOError:
            print("saving the network failed")

    def load_network_from_file(self, step, game_type):
        """
        Deserializes the Neural Network,
        and loads it from a file, based on the given step number.
        This network is then returned.
        """
        folder_name = "../resources/"
        data_type = "/networks/"
        file_name = "network"

        try:
            set_nn_config()
            if step is None:
                #gets the most recently created network's path, and finds its step count, based on file name, and sets current_step to this int. 
                list_of_files = glob(folder_name + game_type + data_type + "*")
                latest_file = max(list_of_files, key=os.path.getmtime)
                s = os.path.basename(latest_file)
                step_string = s.replace(file_name, "")
                current_step = int(step_string, base=10)
                self.curr_step = current_step
            else:
                #if a step is given, use this step
                current_step = step
                self.curr_step = current_step
            version_nn = str(current_step)

            network_model = load_model(folder_name + game_type + data_type + file_name + str(version_nn), None, True)
            print("Neural Network was loaded from file")
            return network_model
        except IOError:
            if not os.path.exists((folder_name + game_type + data_type + file_name + str(version_nn))):
                print("network file was not found: " + folder_name + game_type + data_type + file_name + str(version_nn))
            else:
                print("file was found, but something else went wrong")

    def load_macro_network_from_file(self, step, game_type):
        """
        Deserializes the Neural Network, from the macro folder,
        and loads it from a file, based on the given step number.
        This network is then returned.
        """
        folder_name = "../resources/"
        data_type = "/macroNetworks/"
        file_name = "network"
        current_step = step
        try:
            if step is None:
                current_step = len(glob(folder_name + game_type + data_type + "*"))-1
                self.curr_step = current_step
            elif step % Config.SAVE_CHECKPOINT_MACRO != 0:
                current_step = step - (step % Config.SAVE_CHECKPOINT_MACRO)
            else:
                current_step = step
            version_nn = str(current_step)

            network_model = load_model(folder_name + game_type + data_type + file_name + str(version_nn), None, True)
            print(f"Macro Neural Network was loaded from file at step {current_step}")
            return network_model, current_step
        except IOError:
            if not os.path.exists((folder_name + game_type + data_type + file_name + str(version_nn))):
                print("macro network file was not found: " + folder_name + game_type + data_type + file_name + str(version_nn))
            else:
                print("file was found, but something else went wrong")

    def save_network_to_sql(self, network):
        print("save_network_to_sql called")
        filename = "network"
        
        config = network.model.get_config()
        data = pickle.dumps(config)
        
        sql_conn = SqlUtil.connect()
        SqlUtil.network_data_insert_row(sql_conn, TimerUtil.get_computer_hostname(), filename, "saved neural network",  data)
        print("Network inserted into sql database table")

    def load_newest_network_from_sql(self):
        sql_conn = SqlUtil.connect()
        network_tuple = SqlUtil.network_data_select_newest_network(sql_conn) #dont know what datatype is returned from fetchone(), it seems to be a tuple
        network_config = network_tuple[0]

        config = pickle.loads(network_config)
        network_model = Model.from_config(config)
        print("Newest network selected from sql database table")
        return network_model
