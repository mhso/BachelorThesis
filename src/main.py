"""
----------------------------------------
main: Run game iterations and do things.
----------------------------------------
"""
import pickle
import threading
from glob import glob
from sys import argv
from os import mkdir
from os.path import exists
from controller.latrunculi import Latrunculi
from controller.minimax import Minimax
from controller.mcts import MCTS
from controller.random import Random

from view.visualize import Gui

def play_game(game, player_white, player_black, gui=None):
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
        
        if gui is not None:
            gui.update(state)

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

class SupportThread(threading.Thread):
    def __init__(self, args):
        threading.Thread.__init__(self)
        self.args = args

    def run(self):
        play_game(self.args[0], self.args[1], self.args[2], self.args[7])
        train(self.args[0], self.args[1], self.args[2], self.args[3], self.args[4], self.args[5], self.args[6], self.args[7])

def train(game, p1, p2, type1, type2, iteration, save=False, gui=None):
    """
    Run a given number of game iterations with a given AI.
    After each game iteration, if the model is MCTS,
    we save the model for later use. If 'load' is true,
    we load these MCTS models.
    """
    if iteration == 0:
        return
    try:
        if gui is not None:
            t = SupportThread((game, p1, p2, type1, type2, iteration, save, gui))
            t.start()
            gui.run()
        else:
            play_game(game, p1, p2)
            train(game, p1, p2, type1, type2, iteration-1, save, gui)
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
                
                if not exists(MCTS_PATH):
                    mkdir(MCTS_PATH)
                save_models(p1, MCTS_PATH+"mcts_{}".format(leading_zeros(len(models) + iteration + 1)))

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
    elif lower == "human":
        return None, "Human"
    elif lower == "random":
        return Random(game), "Random"
    return None, "unknown"

# Load arguments for running the program.
# The args, in order, correspond to the variables below.
player1 = "."
player2 = "."
game_name = "."
board_size = 8
rand_seed = None

wildcard = "."
option_list = ["-s", "-l", "-d", "-g"]
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

if "-l" in options:
    MCTS_PATH = "../resources/"
    models = glob(MCTS_PATH+"/mcts*")
    if len(models) > 0:
        if player1 == "mcts":
            p_white.state_map = load_model(models[-1])
        if player2 == "mcts":
            p_black.state_map = load_model(models[-1])

gui = None
if "-g" in options or player1.lower() == "human" or player2.lower() == "human":
    gui = Gui(game)
    game.register_observer(gui)

train(game, p_white, p_black, player1.lower(), player2.lower(), 1, "-s" in options, gui)
