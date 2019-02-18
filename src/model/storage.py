"""
storage: Stores/saves/loads neural network models for use in
training and self-play, as well as replay buffers generated from self-play.
"""
import numpy as np
import constants
from model.neural import NeuralNetwork

class ReplayStorage:
    """
    This class manages the saving/loading of replays from games.
    """
    def __init__(self):
        self.max_games = constants.MAX_GAME_STORAGE
        self.batch_size = constants.BATCH_SIZE
        self.buffer = []

    def save_game(self, game):
        if len(self.buffer) > self.max_games:
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
        move_sum = float(sum(len(g.history()) for g in self.buffer))
        # Draw random games, with each game weighed according to the amount
        # of moves made in that game.
        batch = np.random.choice(
            self.buffer,
            size=self.batch_size,
            p=[len(g.history())/move_sum for g in self.buffer]
        )
        # Draw random state index values from all chosen games.
        state_indices = [(g, np.random.randint(0, len(g.history()))) for g in batch]
        images = []
        targets = []
        # Create input/expected output data for neural network training.
        for game, index in state_indices:
            images.append(game.structure_data(game.history[index]))
            targets.append(game.make_target(index))
        return np.array(images), np.array(targets)

class NetworkStorage:
    """
    This class manages the saving/loading of neural networks.
    The network periodically saves it's model to this class and
    MCTS loads the newest network during self-play.
    """
    networks = {}
    curr_network = None

    def latest_network(self):
        if self.networks == {}:
            return NeuralNetwork()
        return self.latest_network

    def save_network(self, step, network):
        self.networks[step] = network
        self.curr_network = network
