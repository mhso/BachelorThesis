"""
Constants for days.
"""
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
# Max number of moves in Latrunculi before a draw
# is assigned.
LATRUNCULI_MAX_MOVES = 200

# Training iterations (for each thread), so total games
# run will equal GAME_THREADS * TRAINING_ITERATIONS.
TRAINING_ITERATIONS = 10

# Amount of games to run in parallel during training.
# 1 = no parallel games.
GAME_THREADS = 1

# How often to evaluate model against base AI's
# during training, default is every 5th training iteration.
EVAL_CHECKPOINT = 0

# How many games to play against base AI's while
# evaluating model performance (per thread).
EVAL_ITERATIONS = 5

# |***********************************|
# |      NEURAL NETWORK OPTIONS       |
# |***********************************|
# How often to save neural network to shared storage.
SAVE_CHECKPOINT = 10

# Amount of games stored, at one time, in replay storage.
MAX_GAME_STORAGE = 100 # Is 1 million in AlphaZero, scale accordingly.

# Batch size for neural network input.
BATCH_SIZE = 256

# Learning rate(s).
LEARNING_RATE = 2e-1

# Momentum for SGD optimization.
MOMENTUM = 0.9

# Weight decay.
WEIGHT_DECAY = 1e-4

# |***********************************|
# |           MCTS OPTIONS            |
# |***********************************|
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
