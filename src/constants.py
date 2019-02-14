"""
Constants for days.
"""
# Default AI algorithm.
DEFAULT_AI = "MCTS"

# Default Game to play.
DEFAULT_GAME = "Latrunculi"

# Default board size.
DEFAULT_BOARD_SIZE = 8

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
# evaluating model performance.
EVAL_ITERATIONS = 5