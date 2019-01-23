"""
----------------------------------------
main: Run game iterations and do things.
----------------------------------------
"""
from sys import argv
from controller.latrunculi import Latrunculi
from controller.minimax import Minimax

def play_game(game, player1, player2):
    """
    Play a game to the end, and return the reward for each player.
    """
    state = game.start_state()
    while not game.terminal_test(state):
        print("Game move")
        if game.player(state):
            state = player1.execute_action(state)
        else:
            state = player2.execute_action(state)

    # Return reward/punishment for player1 and player2.
    return game.utility(player1), game.utility(player2)

def get_game(game_name, size, rand_seed):
    if game_name.lower() == "latrunculi":
        return Latrunculi(size, rand_seed)
    return None

def get_ai_algorithm(algorithm, game):
    if algorithm.lower() == "minimax":
        return Minimax(game)
    return None

# Load arguments for running the program.
# The args, in order, correspond to the variables below.
player1 = "minimax"
player2 = "minimax"
game_name = "latrunculi"
board_size = 8
rand_seed = None

argc = len(argv)
if argc > 1:
    player1 = argv[1] # Algorithm playing as player 1.

    if argc == 2 or argc == 3:
        game = Latrunculi(board_size)
        if argc == 2: # If only one player is given, player 2 will be the same algorithm.
            player2 = player1
    if argc > 2:
        player2 = argv[2] # Algorithm playing as player 2.

        if argc > 3:
            game_name = argv[3] # Game to play.
            if argc > 4:
                board_size = int(argv[4]) # Size of board.

                if argc == 6:
                    rand_seed = int(argv[5])

game = get_game(game_name, board_size, rand_seed)
p1 = get_ai_algorithm(player1, game)
p2 = get_ai_algorithm(player2, game)

print("Playing '{}' with board size {}x{} with '{}' vs. '{}'".format(game_name, board_size, board_size, player1, player2))
play_game(game, p1, p2)
