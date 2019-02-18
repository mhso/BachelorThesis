"""
storage: Stores/saves/loads neural network models for use in 
training and self-play, as well as replay buffers generated from self-play.
"""
import constants

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
        return None

class NetworkStorage:
    """
    This class manages the saving/loading of neural networks.
    """
    networks = {}
    pass
