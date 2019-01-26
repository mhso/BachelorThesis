"""
----------------------------------------
main: Run game iterations and do things.
----------------------------------------
"""
import pickle
from glob import glob
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

def leading_zeros(num):
    result = str(num)
    if num < 1000:
        result = "0" + result
    if num < 100:
        result = "0" + result
    if num < 10:
        result = "0" + result
    return result

def train(game, p1, p2, type1, type2, iterations, load=False, save=False):
    """
    Run a given number of game iterations with a given AI.
    After each game iteration, if the model is MCTS,
    we save the model for later use. If 'load' is true,
    we load these MCTS models.
    """
    MCTS_PATH = "../resources/mcts"
    models = glob(MCTS_PATH+"*")
    if load:
        if type1 == "mcts":
            p1.state_map = load_model(models[-1])
        if type2 == "mcts":
            p2.state_map = load_model(models[-1])

    for i in range(iterations):
        try:
            play_game(game, p1, p2)
        except KeyboardInterrupt:
            pass
        finally:
            if save:
                if type1 == "mcts" or type2 == "mcts":
                    state_map = None
                    if type1 == "mcts":
                        state_map = p1.state_map
                        if type2 == "mcts":
                            state_map = state_map.update(p2.state_map)
                    else:
                        state_map = p2.state_map
                    save_models(p1, MCTS_PATH+"_{}".format(leading_zeros(len(models) + i + 1)))

def save_models(model, path):
    print("Saving model to file: {}".format(path))
    pickle.dump(model.state_map, open(path, "wb"))

def load_model(path):
    print("Loading model from file: {}".format(path))
    return pickle.load(open(path, "rb"))

def get_game(game_name, size, rand_seed, wildcard):
    lower = game_name.lower()
    if lower in ("latrunculi", wildcard):
        return Latrunculi(size, rand_seed), "Latrunculi"
    return None, "unknown"

def get_ai_algorithm(algorithm, game, wildcard):
    lower = algorithm.lower()
    if lower in ("mcts", wildcard):
        return MCTS(game), "MCTS"
    elif lower == "minimax":
        return Minimax(game), "Minimax"
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
option_list = ["-s", "-l", "-d"]
options = []
args = []
# Seperate arguments from options.
for s in argv:
    if s in option_list:
        options.append(s)
    else:
        args.append(s)

argc = len(args)
if argc > 1:
    if args[1] in ("-help", "-h"):
        print("Usage: {} [player1] [player2] [game] [board_size] [rand_seed] [options...]".format(args[0]))
        print("Write '{}' in place of any argument to use default value".format(wildcard))
        print("Options: -d (debug), -s (save models), -l (load models)")
        print("Fx. 'python {} minimax . latrunculi 8 42'".format(args[0]))
        exit(0)
    player1 = args[1] # Algorithm playing as player 1.

    if argc == 2 or argc == 3:
        game = Latrunculi(board_size)
        if argc == 2: # If only one player is given, player 2 will be the same algorithm.
            player2 = player1
    if argc > 2:
        player2 = args[2] # Algorithm playing as player 2.

        if argc > 3:
            game_name = args[3] # Game to play.
            if argc > 4:
                if args[4] != wildcard:
                    board_size = int(args[4]) # Size of board.

                if argc > 5 and args[5] != wildcard:
                    rand_seed = int(args[5])

game, game_name = get_game(game_name, board_size, rand_seed, wildcard)
p_white, player1 = get_ai_algorithm(player1, game, wildcard)
p_black, player2 = get_ai_algorithm(player2, game, wildcard)

print("Playing '{}' with board size {}x{} with '{}' vs. '{}'".format(game_name, board_size, board_size, player1, player2))
train(game, p_white, p_black, player1.lower(), player2.lower(), 1, "-l" in options, "-s" in options)
