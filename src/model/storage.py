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
        # TODO: Add a threading lock instead of copying buffer??
        copy_buffer = [g for g in self.buffer]
        # Sum up how many moves were made during all games in the buffer.
        move_sum = float(sum(len(g.history) for g in copy_buffer))
        # Draw random games, with each game weighed according to the amount
        # of moves made in that game.
        batch = np.random.choice(
            copy_buffer,
            size=self.batch_size,
            p=[len(g.history)/move_sum for g in copy_buffer]
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
        serializes a game, and saves it to a file, under the correct neural network version, given by the step parameter
        """
        folderName = "resources/replays/"
        versionNN = str(step)
        folderNN = "NNv" + versionNN + "/"
        fileName = "game"
        fileExtension = ".txt"
        print("save_replay was called")

        numberOfFiles = (glob(folderName + folderNN + "*" + fileExtension)).__len__()
        gameNumber = numberOfFiles+1

        if not os.path.exists((folderName + folderNN)):
            os.makedirs((folderName + folderNN))

        try:
            newFile = open((folderName + folderNN + fileName + str (gameNumber) + fileExtension), "xb")
            pickle.dump(game, newFile)
            newFile.close()
        except:
            print("something went wrong, when trying to save a replay")

    def load_replay(self, step):
        """
        method for loading saved games back into Replay Storage buffer.
        The method selects the newest NN version, where the amount of saved games
        is less than the constant MAX_GAME_STORAGE, it then loads the games directly into the buffer.
        The "step" parameter, defines the newest NN version we are interested in
        """
        folderName = "resources/replays/"
        folderNNNoVersion = "NNv"
        fileExtension = ".txt"

        try:
            if step is None:
                currentStep = (glob(folderName)).__len__()
            else:
                currentStep = step

            stepCounter = currentStep
            fileCounter = 0
            while stepCounter > 0 and fileCounter < constants.MAX_GAME_STORAGE:
                fileList = glob(folderName + folderNNNoVersion + str(stepCounter) + "/" + "*" + fileExtension)

                for f in fileList:
                    if fileCounter < constants.MAX_GAME_STORAGE:
                        openFile = open(f, "rb")
                        game = pickle.load(openFile)
                        self.buffer.append(game)
                        fileCounter += 1
                    else:
                        break
                stepCounter -= 1 
        except:
            print("something went wrong when trying to load games into buffer")


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
        self.curr_step = step

    def replace_dummy_network(self):
        old_network = self.latest_network()
        network = NeuralNetwork(old_network.board_size, old_network.action_space, False)
        self.save_network(self.curr_step, network)

    def save_network_to_file(self, step, network):
        """
        serializes the Neural Network, and saves it to a file, under the correct version, given by the step parameter
        """
        folderName = "resources/networks/"
        versionNN = str(step)
        fileName = "network"

        if not os.path.exists((folderName)):
            os.makedirs((folderName))
        try:
            save_model(network, (folderName + fileName + str(versionNN)), True, True)
        except:
            print("saving the network failed")

    def load_network_from_file(self, step):
        """
        Deserializes the Neural Network, and loads it from a  file, based on the given step number.
        This network is then returned
        """
        folderName = "resources/networks/"
        versionNN = str(step)
        fileName = "network"

        try:
            network = load_model((folderName + fileName + str(versionNN)), None, True)
            print("Network was loaded from file")
            return network
        except:
            if not os.path.exists((folderName + fileName + str(versionNN))):
                print("network file was not found: " + (folderName + fileName + str(versionNN)))
            else:
                print("file was found, but something else went wrong")
        

