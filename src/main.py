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
from time import sleep, time
from controller.latrunculi import Latrunculi
from controller.mcts import MCTS
from view.log import log
from view.visualize import Gui
from view.graph import Graph

def force_quit(gui):
    return gui is not None and not gui.active or Graph.stop_event.is_set()

def plot_game_result(game, result, p_white, p_black):
    white_win = game.utility(result, p_white)
    black_win = game.utility(result, p_black)
    draw = not white_win and not black_win
    Graph.plot_data() # SOMETHING

def play_game(game, player_white, player_black, gui=None):
    """
    Play a game to the end, and return the reward for each player.
    """
    state = game.start_state()
    max_iter = 1000
    counter = 0
    time_game = time()
    sleep(1)
    if gui is not None:
        gui.update(state) # Update GUI, to clear board, if several games are played sequentially.

    while not game.terminal_test(state) and counter < max_iter:
        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        print("Player: {}".format(state.str_player()), flush=True)
        num_white, num_black = state.count_pieces()
        print("Num of pieces, White: {} Black: {}".format(num_white, num_black), flush=True)
        time_turn = time()

        if game.player(state):
            state = player_white.execute_action(state)
        else:
            state = player_black.execute_action(state)

        if "-t" in argv:
            log("Move took: {} s".format(time() - time_turn))

        if force_quit(gui):
            print("Forcing exit...")
            exit(0)

        if gui is not None:
            if type(player_white).__name__ != "Human" and not state.player:
                sleep(0.5)
            elif type(player_black).__name__ != "Human" and state.player:
                sleep(0.5)
            gui.update(state)
        else:
            print(state.board, flush=True)
        counter += 1

    winner = "Black" if state.player else "White"
    print("LADIES AND GENTLEMEN, WE GOT A WINNER: {}!!!".format(winner), flush=True)
    print(state.board, flush=True)
    if "-t" in argv:
        print("Game took {} s.".format(time() - time_game), flush=True)
    # Return resulting state of game.
    return state

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
        play_game(self.args[0], self.args[1], self.args[2], self.args[5])
        train(self.args[0], self.args[1], self.args[2], self.args[3], self.args[4], self.args[5], self.args[6])

def train(game, p1, p2, iteration, save=False, gui=None, plot_data=False):
    """
    Run a given number of game iterations with a given AI.
    After each game iteration, if the model is MCTS,
    we save the model for later use. If 'load' is true,
    we load these MCTS models.
    """
    if iteration == 0:
        return
    try:
        if gui is not None or plot_data:
            # If GUI is used, (and if a non-human is playing),
            # create seperate thread to run the AI game logic in.
            game_thread = SupportThread((game, p1, p2, iteration-1, save, gui, plot_data))
            game_thread.start() # Start game logic thread.
            if gui is not None:
                gui.run() # Start GUI on main thread.
        else:
            play_game(game, p1, p2)
            train(game, p1, p2, iteration-1, save, gui)
    except KeyboardInterrupt:
        print("Exiting by interrupt...")
        if gui is not None:
            gui.close()
        if plot_data:
            Graph.close()
        exit(0)
    finally:
        if save:
            type1 = type(p1).__name__
            type2 = type(p2).__name__
            if type1 == "MCTS" or type2 == "MCTS":
                state_map = None
                if type1 == "mcts":
                    state_map = p1.state_map
                    if type2 == "mcts":
                        state_map = state_map.update(p2.state_map)
                else:
                    state_map = p2.state_map

                if not exists(MCTS_PATH):
                    mkdir(MCTS_PATH)
                save_models(state_map, MCTS_PATH+"mcts_{}".format(leading_zeros(len(models) + 1)))

def save_models(model, path):
    print("Saving model to file: {}".format(path), flush=True)
    pickle.dump(model, open(path, "wb"))

def load_model(path):
    print("Loading model from file: {}".format(path), flush=True)
    return pickle.load(open(path, "rb"))

def get_game(game_name, size, rand_seed, wildcard):
    lower = game_name.lower()
    if lower == wildcard:
        return Latrunculi(size, rand_seed)
    try:
        module = __import__("controller.{}".format(lower), fromlist=["{}".format(game_name)])
        algo_class = getattr(module, "{}".format(game_name))
        return algo_class(size, rand_seed)
    except ImportError:
        print("Unknown game, name must equal name of game class.")
        return None, "unknown"

def get_ai_algorithm(algorithm, game, wildcard, gui=None):
    lower = algorithm.lower()
    if lower == wildcard:
        return MCTS(game)
    try:
        module = __import__("controller.{}".format(lower), fromlist=["{}".format(algorithm)])
        algo_class = getattr(module, "{}".format(algorithm))
        return algo_class(game)
    except ImportError:
        print("Unknown AI algorithm, name must equal name of AI class.")
        return None, "unknown"

# Load arguments for running the program.
# The args, in order, correspond to the variables below.
player1 = "."
player2 = "."
game_name = "."
board_size = 8
rand_seed = None

wildcard = "."
option_list = ["-s", "-l", "-v", "-t", "-g", "-p"]
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
        print("Options: -v (verbose), -t (time operations), -s (save models), -l (load models), -g (use GUI), -p (plot data)")
        print("Fx. 'python {} Minimax MCTS Latrunculi . 42 -g'".format(args[0]))
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

game = get_game(game_name, board_size, rand_seed, wildcard)
p_white = get_ai_algorithm(player1, game, wildcard)
p_black = get_ai_algorithm(player2, game, wildcard)

print("Playing '{}' with board size {}x{} with '{}' vs. '{}'".format(type(game).__name__, board_size, board_size, type(p_white).__name__, type(p_black).__name__))
player1 = player1.lower()
player2 = player2.lower()

if "-l" in options:
    MCTS_PATH = "../resources/"
    models = glob(MCTS_PATH+"/mcts*")
    if models != []:
        if player1 == "mcts":
            p_white.state_map = load_model(models[-1])
        if player2 == "mcts":
            p_black.state_map = load_model(models[-1])

gui = None
if "-g" in options or player1 == "human" or player2 == "human":
    gui = Gui(game)
    game.register_observer(gui)
    if player1 == "human":
        p_white.gui = gui
    if player2 == "human":
        p_black.gui = gui

if "-p" in options:
    Graph.run(gui) # If we should plot data, start graph window in main thread.

train(game, p_white, p_black, 3, "-s" in options, gui, "-p" in options)
