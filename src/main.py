"""
----------------------------------------
main: Run game iterations and do things.
----------------------------------------
"""
from sys import argv
from controller.latrunculi import Latrunculi
from controller.minimax import Minimax
from controller.mcts import MCTS
from controller.random import Random
#from view.visualize import Gui

def play_game(game, player_white, player_black):
    """
    Play a game to the end, and return the reward for each player.
    """
    state = game.start_state()
    while not game.terminal_test(state):
        print(state, flush=True)
        if game.player(state):
            state = player_white.execute_action(state)
            #print(player_white, flush=True)
        else:
            state = player_black.execute_action(state)
            #print(player_black, flush=True)

    winner = "Black" if state.player else "White"
    print("LADIES AND GENTLEMEN, WE GOT A WINNER: {}!!!".format(winner))
    # Return reward/punishment for player1 and player2.
    return game.utility(state, player1), game.utility(state, player2)

def get_game(game_name, size, rand_seed, wildcard):
    lower = game_name.lower()
    if lower in ("latrunculi", wildcard):
        return Latrunculi(size, rand_seed), "Latrunculi"
    return None, "unknown"

def get_ai_algorithm(algorithm, game, wildcard):
    lower = algorithm.lower()
    if lower in ("minimax", wildcard):
        return Minimax(game), "Minimax"
    elif lower == "mcts":
        return MCTS(game), "MCTS"
    elif lower == "random":
        return Random(game), "Random"
    return None, "unknown"

# Load arguments for running the program.
# The args, in order, correspond to the variables below.
player1 = "minimax"
player2 = "minimax"
game_name = "latrunculi"
board_size = 8
rand_seed = None

wildcard = "."
argc = len(argv)
if argc > 1:
    if argv[1] in ("-help", "-h"):
        print("Usage: {} [white_player] [black_player] [game] [board_size] [rand_seed].".format(argv[0]))
        print("Write '{}' in place of any argument to use default value.".format(wildcard))
        print("Fx. 'python {} minimax . latrunculi 8 42'".format(argv[0]))
        exit(0)
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
                if argv[4] != wildcard:
                    board_size = int(argv[4]) # Size of board.

                if argc == 6 and argv[5] != wildcard:
                    rand_seed = int(argv[5])

game, game_name = get_game(game_name, board_size, rand_seed, wildcard)
p_white, player1 = get_ai_algorithm(player1, game, wildcard)
p_black, player2 = get_ai_algorithm(player2, game, wildcard)

print("Playing '{}' with board size {}x{} with '{}' vs. '{}'".format(game_name, board_size, board_size, player1, player2))
play_game(game, p_white, p_black)
