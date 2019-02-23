"""
storage: Stores/saves/loads neural network models for use in
training and self-play, as well as replay buffers generated from self-play.
"""
import numpy as np
import constants
from model.neural import NeuralNetwork, DummyNetwork

class ReplayStorage:
    """
    This class manages the saving/loading of replays from games.
    """
    def __init__(self):
        self.max_games = constants.MAX_GAME_STORAGE
        self.batch_size = constants.BATCH_SIZE
        self.buffer = []
        self.perform_eval_buffer = []

    def save_game(self, game):
        if len(self.buffer) > self.max_games:
            self.buffer.pop(0) # Remove oldest game.
        self.buffer.append(game)
        #print("Saved game to buffer. Games: {}".format(len(self.buffer)), flush=True)

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

    def save_perform_eval_data(self, data):
        buff = self.perform_eval_buffer
        buff.append(data)

    def eval_performance(self):
        return len(self.perform_eval_buffer) >= constants.EVAL_ITERATIONS * constants.GAME_THREADS

    def reset_perform_data(self):
        data = self.perform_eval_buffer
        self.perform_eval_buffer = []
        return data

class NetworkStorage:
    """
    This class manages the saving/loading of neural networks.
    The network periodically saves it's model to this class and
    MCTS loads the newest network during self-play.
    """
    def __init__(self, game_size, action_space=4):
        self.networks = {}
        self.curr_step = 0
        self.game_size = game_size

    def latest_network(self):
        if self.networks == {}:
            self.save_network(0, NeuralNetwork(self.game_size))
        return self.networks[self.curr_step]

    def save_network(self, step, network):
        self.networks[step] = network
        self.curr_step = step
