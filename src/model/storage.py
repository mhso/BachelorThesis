"""
storage: Stores/saves/loads neural network models for use in
training and self-play, as well as replay buffers generated from self-play.
"""
from multiprocessing import Queue
import numpy as np
import constants

class ReplayStorage:
    """
    This class manages the saving/loading of replays from games.
    """
    def __init__(self):
        self.max_games = constants.MAX_GAME_STORAGE
        self.batch_size = constants.BATCH_SIZE
        self.buffer = Queue(constants.MAX_GAME_STORAGE)
        self.perform_eval_buffer = Queue(constants.EVAL_ITERATIONS * constants.GAME_THREADS)

    def save_game(self, game):
        if self.buffer.full():
            self.buffer.get() # Remove oldest game (maybe).
        self.buffer.put(game)

    def sample_batch(self):
        """
        Draw a set amount of random samples from the saved games.
        @returns - A tuple of two arrays, one with input data for
        the neural network and one with a corresponding list of
        expected outcomes of the game + move probability distribution.
        """
        # TODO: Add a threading lock instead of copying buffer??
        copy_buffer = Queue(constants.MAX_GAME_STORAGE)
        buffer_arr = []
        while not self.buffer.empty():
            game = self.buffer.get()
            copy_buffer.put(game)
            buffer_arr.append(game)
        self.buffer = copy_buffer

        # Sum up how many moves were made during all games in the buffer.
        move_sum = float(sum(len(g.history) for g in buffer_arr))
        # Draw random games, with each game weighed according to the amount
        # of moves made in that game.
        batch = np.random.choice(
            buffer_arr,
            size=self.batch_size,
            p=[len(g.history)/move_sum for g in buffer_arr]
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
        return self.buffer.full()

    def save_perform_eval_data(self, data):
        self.perform_eval_buffer.put(data)

    def eval_performance(self):
        return self.perform_eval_buffer.full()

    def reset_perform_data(self):
        data = []
        while not self.perform_eval_buffer.empty():
            data.append(self.perform_eval_buffer.get())
        return data

class NetworkStorage:
    """
    This class manages the saving/loading of neural networks.
    The network periodically saves it's model to this class and
    MCTS loads the newest network during self-play.
    """
    def __init__(self):
        self.networks = Queue(constants.TRAINING_STEPS // constants.SAVE_CHECKPOINT)
        print(hash(self.networks))

    def is_empty(self):
        return self.networks.empty()

    def latest_network(self):
        step, network = self.networks.get()
        self.networks.put((step, network))
        return network

    def save_network(self, step, network):
        self.networks.put((step, network))

    #def replace_dummy_network(self):
    #    old_network = self.latest_network()
    #    network = NeuralNetwork(old_network.board_size, old_network.action_space, False)
    #    self.save_network(self.networks.qsize, network)
