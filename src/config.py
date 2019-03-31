"""
Constants for days.
"""
class Config():
    def __init__(self, kvargs=None):
        if kvargs:
            for k, v in kvargs.items():
                setattr(Config, k, v)
                self.__setattr__(k, v)

    # |***********************************|
    # |          CMD ARG OPTIONS          |
    # |***********************************|
    # Default AI algorithm.
    DEFAULT_AI = "MCTS"

    # Default Game to play.
    DEFAULT_GAME = "Latrunculi"

    # Default board size.
    DEFAULT_BOARD_SIZE = 4

    # |***********************************|
    # |    TRAINING/GAME LOOP OPTIONS     |
    # |***********************************|
    # Save training progress to DB.
    STATUS_DB = False

    # Max number of moves in Latrunculi before a draw
    # is assigned.
    LATRUNCULI_MAX_MOVES = 200

    # Number of training steps for the neural network.
    TRAINING_STEPS = 500

    # Number of games to play in self-play (for each thread),
    # so total games run will equal GAME_THREADS * GAME_ITERATIONS.
    # If set to -1, self-play will run indefinitely.
    GAME_ITERATIONS = -1

    # Amount of games to run in parallel during training.
    # 1 = no parallel games.
    GAME_THREADS = 8

    # How many games to generate per training run.
    # Default is to run training every time all processes
    # has completed a game.
    GAMES_PER_TRAINING = 8

    # How often to evaluate model against base AI's
    # during training, default is every 5th training iteration.
    EVAL_CHECKPOINT = {0: 30, 50: 50, 150: 70}

    # How many games to play against each base AI
    # while evaluating model performance.
    # Should be a multiple of EVAL_PROCESSES (below).
    EVAL_GAMES = 16

    # How many processes that should run evaluation games.
    EVAL_PROCESSES = 4

    # |***********************************|
    # |      NEURAL NETWORK OPTIONS       |
    # |***********************************|
    # Fraction of GPU memory TensorFlow is allowed to use.
    MAX_GPU_FRACTION = 0.5

    # How often to save neural network to shared storage.
    SAVE_CHECKPOINT = 1

    # How often to save neural network to the shared storage for macro Networks,
    # where we save significant generations of the network.
    SAVE_CHECKPOINT_MACRO = 100

    # Amount of games stored, at one time, in replay storage.
    MAX_GAME_STORAGE = 500 # Is 1 million in AlphaZero, scale accordingly.S

    # Amount of netwroks stored at one time in network storage.
    MAX_NETWORK_STORAGE = 10

    # Batch size for neural network input.
    BATCH_SIZE = 256

    # Number of times to train per training step.
    ITERATIONS_PER_TRAINING = 5

    # Number of times to train on one batch.
    EPOCHS_PER_BATCH = 3

    # Fraction of training data to validate on.
    VALIDATION_SPLIT = 0.2

    # Learning rate(s).
    LEARNING_RATE = 1e-1

    # Momentum for SGD optimization.
    MOMENTUM = 0.9

    # Weight decay.
    WEIGHT_DECAY = 1e-4

    # Amount of filters to use in convolutional layers.
    CONV_FILTERS = 128

    # Number of residual layers.
    RES_LAYERS = 11

    # Use bias.
    USE_BIAS = False

    # Kernel initializer.
    # Options:0 'uniform', 'normal'.
    WEIGHT_INITIALIZER = "uniform"

    REGULARIZER_CONST = 0.0001

    # |***********************************|
    # |           MCTS OPTIONS            |
    # |***********************************|
    # Number of iterations per action taken.
    MCTS_ITERATIONS = 800

    # Base exploration constant. This basically defines how much the visit
    # count for a node in MCTS should count towards it's UCB score. Lowering
    # this number means that when the visit count of a node increases, it's
    # UCB score increases faster.
    EXPLORE_BASE = 19652

    # Base value for the exploration parameter described above.
    EXPLORE_INIT = 1.25

    # When selecting a final action in MCTS, if the game has had less than
    # this amount of moves, we select a random available action, weighted by
    # visit count for the node associated with that action. Otherwise we select
    # the action associated with the node with most visits.
    NUM_SAMPLING_MOVES = 30

    # Exploration noise to encourage exploring new nodes.
    NOISE_BASE = 0.3

    NOISE_FRACTION = 0.25

    # |***********************************|
    # |           SELF PLAY               |
    # |***********************************|

    # Sleep delay for when an AI is playing with gui
    GUI_AI_SLEEP = 0.5

    @staticmethod
    def from_file(filename):
        try:
            with open(filename) as f:
                lines = f.readlines()
                kv_args = dict()
                for line in lines:
                    kv_split = line.split("=")
                    k = kv_split[0].strip()
                    v = try_parse(kv_split[1].strip())
                    kv_args[k] = v
                return Config(kv_args)
        except FileNotFoundError:
            print("Error: Config file not found!")
        except IOError:
            print("Error: Invalid config file!")

def try_parse(val):
    try:
        to_int = int(val)
        return to_int
    except ValueError:
        try:
            to_float = float(val)
            return to_float
        except ValueError:
            lower = val.lower()
            if lower in ("true", "false"):
                return lower == "true"
            return val

def set_game_specific_values(cfg, game):
    """
    Is called from main. Sets game specific
    config values such as NOISE_BASE used
    when applying Dirichlet noise.
    """
    game_name = type(game).__name__

    noise = 0.3
    sample_moves = 30
    if game_name == "Latrunculi":
        # Noise values for board sizes 4-8.
        # Values are based on an average action space of
        # 8, 14, 22, 30, and 40.
        noise_options = [1.25, 0.7, 0.45, 0.33, 0.25]
        # Values for minimum moves for argmax of visits in MCTS.
        # Values are based on the average game length of
        # 300, 1200, 1600, 2400, and 5000.
        sampling_options = [30, 120, 160, 240, 500]
        noise = noise_options[8-game.size]
        sample_moves = sampling_options[8-game.size]
    elif game_name == "Othello":
        # Avg actions: 4, 6, 9, 11, and 14.
        noise_options = [2.5, 1.66, 1.11, 0.9, 0.7]
        # Avg game length: 10, 20, 30, 45, and 60.
        sampling_options = [2, 3, 4, 5, 7]
        noise = noise_options[8-game.size]
        sample_moves = sampling_options[8-game.size]
    elif game_name == "Connect_Four":
        # Avg game length: 40, 22, 18, 15, and 10.
        sampling_options = [3, 2, 2, 2, 2]
        # Avg actions are always equal to board size.
        noise = 10/game.size
        sample_moves = sampling_options[8-game.size]
    if cfg:
        cfg.NOISE_BASE = noise
        cfg.NUM_SAMPLING_MOVES = sample_moves
    Config.NOISE_BASE = noise
    Config.NUM_SAMPLING_MOVES = sample_moves
