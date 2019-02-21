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
from model.storage import ReplayStorage, NetworkStorage
from view.log import log
from view.visualize import Gui
from view.graph import Graph
import constants

def force_quit(gui):
    return gui is not None and not gui.active or Graph.stop_event.is_set()

def plot_game_result(result, other):
    Graph.plot_data("Versus {}".format(other), None, result, "Training Iteration", "Winrate")

def play_game(game, player_white, player_black, gui=None):
    """
    Play a game to the end, and return the resulting state.
    """
    state = game.start_state()
    counter = 0
    time_game = time()
    if gui is not None:
        sleep(1)
        gui.update(state) # Update GUI, to clear board, if several games are played sequentially.

    while not game.terminal_test(state) and counter < constants.LATRUNCULI_MAX_MOVES:
        #print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        #print("Player: {}".format(state.str_player()), flush=True)
        num_white, num_black = state.count_pieces()
        #print("Num of pieces, White: {} Black: {}".format(num_white, num_black), flush=True)
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
        counter += 1

    winner = "Black" if state.player else "White"
    print("Game finished on thread {}, winner: {}".format(threading.current_thread().name, winner))
    if "-t" in argv:
        print("Game took {} s.".format(time() - time_game), flush=True)
    #print(state.board, flush=True)

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

def evaluate_against_ai(game, player, other, num_games, step):
    """
    Evaluate MCTS/NN model against a given AI algorithm.
    Plays out a given number of games and returns
    the ratio of games won by MCTS in the range
    -1 to 1, -1 meaning losing all games, 0 meaning
    all games were draws and 1 being winning all games.
    """
    wins = 0
    for _ in range(num_games):
        result = play_game(game, player, other, gui)
        wins += game.utility(result, True)
    return wins/num_games # Return ratio of games won.

def evaluate_model(game, player, storage, show_plot=False):
    """
    Evaluate MCTS/NN model against three different AI
    algorithms. Print/plot result of evaluation.
    """
    step = player.network.curr_step
    eval_minimax = evaluate_against_ai(game, player,
                                       get_ai_algorithm(
                                           "Minimax" if type(game).__name__ == "Latrunculi"
                                           else "Minimax_CF", game, "."),
                                       constants.EVAL_ITERATIONS, step)

    print("Evaluation against Minimax: {}".format(eval_minimax))

    eval_random = evaluate_against_ai(game, player,
                                      get_ai_algorithm("Random", game, "."),
                                      constants.EVAL_ITERATIONS, step)

    print("Evaluation against Random: {}".format(eval_minimax))

    eval_mcts = evaluate_against_ai(game, player,
                                    get_ai_algorithm("MCTS_Basic", game, "."),
                                    constants.EVAL_ITERATIONS, step)

    storage.save_perform_eval_data([eval_minimax, eval_random, eval_mcts])    

    print("Evaluation against MCTS: {}".format(eval_mcts))
    if show_plot and storage.eval_performance():
        data = storage.reset_perform_data()
        Graph.plot_data("Versus Minimax", step, data[0], "Training Iteration", "Winrate")
        Graph.plot_data("Versus Random", step, data[1], "Training Iteration", "Winrate")
        Graph.plot_data("Versus Basic MCTS", step, data[2], "Training Iteration", "Winrate")

class GameThread(threading.Thread):
    def __init__(self, *args):
        threading.Thread.__init__(self)
        self.args = args

    def run(self):
        play_loop(self.args[0], self.args[1], self.args[2], self.args[3], self.args[4], self.args[5], self.args[6], self.args[7])

def play_loop(game, p1, p2, iteration, gui=None, plot_data=False, network_storage=None, replay_storage=None):
    """
    Run a given number of game iterations with a given AI.
    After each game iteration, if the model is MCTS,
    we save the model for later use. If 'load' is true,
    we load these MCTS models.
    """
    if iteration == 0:
        print("{} is done with training!".format(threading.current_thread().name))
        return
    try:
        if network_storage:
            # Set MCTS AI's newest network, if present.
            network = network_storage.latest_network()
            if type(p1).__name__ == "MCTS":
                p1.network = network
            if type(p2).__name__ == "MCTS":
                p2.network = network

        play_game(game, p1, p2, gui)

        if replay_storage:
            # Save game to be used for neural network training.
            replay_storage.save_game(game)
        game.reset() # Reset game history.
        if constants.EVAL_CHECKPOINT and not iteration % constants.EVAL_CHECKPOINT:
            # Evaluate performance of trained model against other AIs.
            evaluate_model(game, p1, replay_storage, plot_data)

        play_loop(game, p1, p2, iteration-1, gui, plot_data)
    except KeyboardInterrupt:
        print("Exiting by interrupt...")
        if gui is not None:
            gui.close()
        if plot_data:
            Graph.close()
        exit(0)

def train_network(network_storage, replay_storage, iterations):
    network = network_storage.latest_network()
    for i in range(iterations):
        if i % constants.SAVE_CHECKPOINT:
            network_storage.save_network(i, network)
        inputs, expected_out = replay_storage.sample_batch()
        network.train(inputs, expected_out)
    network_storage.save_network(iterations, network)

def prepare_training(game, p1, p2, iterations, **kwargs):
    # Extract arguments.
    save = kwargs.get("save", False)
    gui = kwargs.get("gui", None)
    plot_data = kwargs.get("plot_data", False)
    network_storage = kwargs.get("network_storage", None)
    replay_storage = kwargs.get("replay_storage", None)
    if gui is not None or plot_data or constants.GAME_THREADS > 1:
        # If GUI is used, if a non-human is playing, or if
        # several games are being played in parallel,
        # create seperate thread(s) to run the AI game logic in.
        if constants.GAME_THREADS > 1:
            # Don't use plot/GUI if several games are played.
            gui = None

        for i in range(constants.GAME_THREADS):
            if i > 0: # Make copies of game and players.
                copy_game = get_game(type(game).__name__, game.size, None, ".")
                copy_game.init_state = game.start_state()
                game = copy_game
                p1 = get_ai_algorithm(type(p1).__name__, game, ".")
                p2 = get_ai_algorithm(type(p2).__name__, game, ".")
            game_thread = GameThread(game, p1, p2, iterations-1, gui, plot_data, network_storage, replay_storage)
            game_thread.start() # Start game logic thread.

        if network_storage is not None and constants.GAME_THREADS > 1:
            train_network(network_storage, replay_storage, iterations)

        if plot_data:
            Graph.run(gui, "Training Evaluation") # Start graph window in main thread.
        if gui is not None:
            gui.run() # Start GUI on main thread.
    else:
        play_loop(game, p1, p2, iterations-1, network_storage=network_storage, replay_storage=replay_storage)

def save_models(model, path):
    print("Saving model to file: {}".format(path), flush=True)
    pickle.dump(model, open(path, "wb"))

def load_model(path):
    print("Loading model from file: {}".format(path), flush=True)
    return pickle.load(open(path, "rb"))

def get_game(game_name, size, rand_seed, wildcard):
    lower = game_name.lower()
    if lower == wildcard:
        game_name = constants.DEFAULT_GAME
        lower = game_name.lower()
    try:
        module = __import__("controller.{}".format(lower), fromlist=["{}".format(game_name)])
        algo_class = getattr(module, "{}".format(game_name))
        return algo_class(size, rand_seed)
    except ImportError:
        print("Unknown game, name must equal name of game class.")
        return None, "unknown"

def get_ai_algorithm(algorithm, game, wildcard):
    lower = algorithm.lower()
    if lower == wildcard:
        algorithm = constants.DEFAULT_AI
        lower = algorithm.lower()
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
board_size = constants.DEFAULT_BOARD_SIZE
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

print("Playing '{}' with board size {}x{} with '{}' vs. '{}'".format(
    type(game).__name__, board_size, board_size, type(p_white).__name__, type(p_black).__name__), flush=True)
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

NETWORK_STORAGE = None
REPLAY_STORAGE = None
if player1 == "mcts" or player2 == "mcts":
    NETWORK_STORAGE = NetworkStorage()
    REPLAY_STORAGE = ReplayStorage()

TIME_TRAINING = time()

prepare_training(game, p_white, p_black, constants.TRAINING_ITERATIONS,
                 save="-s" in options,
                 gui=gui,
                 plot_data="-p" in options,
                 network_storage=NETWORK_STORAGE,
                 replay_storage=REPLAY_STORAGE)

if "-t" in options:
    print("Training took: {} s".format(time() - TIME_TRAINING))
