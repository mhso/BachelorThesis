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

# How often to evaluate model against base AI's
# during training, default is every 5th training iteration.
EVAL_CHECKPOINT = 5

# How many games to play against base AI's while
# evaluating model performance.
EVAL_ITERATIONS = 3
