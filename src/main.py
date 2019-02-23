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
        log("Num of pieces, White: {} Black: {}".format(num_white, num_black))
        time_turn = time()

        if game.player(state):
            state = player_white.execute_action(state)
        else:
            state = player_black.execute_action(state)

        game.history.append(state)

        if "-t" in argv:
            log("Move took: {} s".format(time() - time_turn))

        if force_quit(gui):
            print("{}: Forcing exit...".format(threading.current_thread().name))
            exit(0)

        if gui is not None:
            if type(player_white).__name__ != "Human" and not state.player:
                sleep(0.5)
            elif type(player_black).__name__ != "Human" and state.player:
                sleep(0.5)
            gui.update(state)
        counter += 1

    winner = "Black" if state.player else "White"
    log("Game finished on thread {}, winner: {}".format(threading.current_thread().name, winner))
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

def evaluate_against_ai(game, player, other, num_games):
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

def evaluate_model(game, player, storage, step, show_plot=False):
    """
    Evaluate MCTS/NN model against three different AI
    algorithms. Print/plot result of evaluation.
    """
    eval_minimax = evaluate_against_ai(game, player,
                                       get_ai_algorithm(
                                           "Minimax" if type(game).__name__ == "Latrunculi"
                                           else "Minimax_CF", game, "."),
                                       constants.EVAL_ITERATIONS)

    print("Evaluation against Minimax: {}".format(eval_minimax))

    eval_random = evaluate_against_ai(game, player,
                                      get_ai_algorithm("Random", game, "."),
                                      constants.EVAL_ITERATIONS)

    print("Evaluation against Random: {}".format(eval_minimax))

    eval_mcts = evaluate_against_ai(game, player,
                                    get_ai_algorithm("MCTS_Basic", game, "."),
                                    constants.EVAL_ITERATIONS)

    storage.save_perform_eval_data([eval_minimax, eval_random, eval_mcts])

    print("Evaluation against MCTS: {}".format(eval_mcts))
    if show_plot and storage.eval_performance():
        data = storage.reset_perform_data()
        Graph.plot_data("Versus Minimax", step, data[0])
        Graph.plot_data("Versus Random", step, data[1])
        Graph.plot_data("Versus Basic MCTS", step, data[2])

class GameThread(threading.Thread):
    def __init__(self, *args):
        threading.Thread.__init__(self)
        self.args = args

    def run(self):
        play_loop(self.args[0], self.args[1], self.args[2], 0, self.args[3], self.args[4], self.args[5], self.args[6])

def play_loop(game, p1, p2, iteration, gui=None, plot_data=False, network_storage=None, replay_storage=None):
    """
    Run a given number of game iterations with a given AI.
    After each game iteration, if the model is MCTS,
    we save the model for later use. If 'load' is true,
    we load these MCTS models.
    """
    if iteration == constants.GAME_ITERATIONS:
        print("{} is done with training!".format(threading.current_thread().name))
        return
    try:
        if network_storage and type(p1).__name__ != "Random":
            # Set MCTS AI's newest network, if present.
            network = network_storage.latest_network()
            if type(p1).__name__ == "MCTS":
                p1.network = network
            if type(p2).__name__ == "MCTS":
                p2.network = network

        play_game(game, p1, p2, gui)

        if replay_storage:
            # Save game to be used for neural network training.
            replay_storage.save_game(game.clone())
            if (type(p1).__name__ == "Random" and constants.RANDOM_INITIAL_GAMES
                    and len(replay_storage.buffer) >= constants.RANDOM_INITIAL_GAMES):
                # We are done with random game generation,
                # moving on to actual self-play.
                network = network_storage.latest_network()
                p1 = get_ai_algorithm("MCTS", game, ".")
                p1.network = network
                p2 = get_ai_algorithm("MCTS", game, ".")
                p2.network = network

        game.reset() # Reset game history.

        if (type(p1).__name__ == "MCTS" and
                constants.EVAL_CHECKPOINT and not iteration % constants.EVAL_CHECKPOINT):
            # Evaluate performance of trained model against other AIs.
            print("Evaluating performance of model on thread {}...".format(threading.current_thread().name), flush=True)
            evaluate_model(game, p1, replay_storage, network_storage.curr_step, plot_data)

        play_loop(game, p1, p2, iteration+1, gui, plot_data, network_storage, replay_storage)
    except KeyboardInterrupt:
        print("Exiting by interrupt...")
        if gui is not None:
            gui.close()
        if plot_data:
            Graph.close()
        exit(0)

def train_network(network_storage, replay_storage, iterations):
    """
    Run a given number of iterations.
    For each iteration, sample a batch of data
    from replay buffer and use the data to train
    the network.
    """
    network = network_storage.latest_network()
    print("NETWORK IS WAITING FOR DATA")
    while len(replay_storage.buffer) < constants.BATCH_SIZE:
        sleep(1)
        if force_quit(None):
            return
    print("NETWORK IS TRAINING", flush=True)

    for i in range(iterations):
        if i % constants.SAVE_CHECKPOINT:
            network_storage.save_network(i, network)
        inputs, expected_out = replay_storage.sample_batch()
        network.train(inputs, expected_out)
        if force_quit(None):
            break
    network_storage.save_network(iterations, network)

def prepare_training(game, p1, p2, **kwargs):
    # Extract arguments.
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
            game_thread = GameThread(game, p1, p2, gui, plot_data, network_storage, replay_storage)
            game_thread.start() # Start game logic thread.

        if network_storage is not None and constants.GAME_THREADS > 1:
            # Run the network training iterations.
            if plot_data:
                train_thread = threading.Thread(target=train_network,
                                                args=(network_storage, replay_storage, constants.TRAINING_STEPS))
                train_thread.start()
            else:
                train_network(network_storage, replay_storage, constants.TRAINING_STEPS)

        if plot_data:
            Graph.run(gui, "Training Evaluation", "Training Iteration", "Winrate") # Start graph window in main thread.
        if gui is not None:
            gui.run() # Start GUI on main thread.
    else:
        play_loop(game, p1, p2, 0, network_storage=network_storage, replay_storage=replay_storage)

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
if type(p_white).__name__ == "MCTS" or type(p_black).__name__ == "MCTS":
    NETWORK_STORAGE = NetworkStorage(game.size)
    REPLAY_STORAGE = ReplayStorage()
    if constants.RANDOM_INITIAL_GAMES:
        if type(p_white).__name__ == "MCTS":
            p_white = get_ai_algorithm("Random", game, ".")
        if type(p_black).__name__ == "MCTS":
            p_black = get_ai_algorithm("Random", game, ".")

TIME_TRAINING = time()

prepare_training(game, p_white, p_black,
                 gui=gui,
                 plot_data="-p" in options,
                 network_storage=NETWORK_STORAGE,
                 replay_storage=REPLAY_STORAGE)

if "-t" in options:
    print("Training took: {} s".format(time() - TIME_TRAINING))
