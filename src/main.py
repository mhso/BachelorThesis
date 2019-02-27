"""
----------------------------------------
main: Run game iterations and do things.
----------------------------------------
"""
import pickle
import threading
from multiprocessing import Queue, Process
from glob import glob
from sys import argv
from time import sleep
from controller.latrunculi import Latrunculi
from controller import self_play
from model.storage import ReplayStorage, NetworkStorage
from model.neural import NeuralNetwork, DummyNetwork
from view.log import log, FancyLogger
from view.visualize import Gui
from view.graph import Graph
import constants

def leading_zeros(num):
    result = str(num)
    if num < 1000:
        result = "0" + result
    if num < 100:
        result = "0" + result
    if num < 10:
        result = "0" + result
    return result

def train_network(network_storage, size, replay_storage, iterations):
    """
    Run a given number of iterations.
    For each iteration, sample a batch of data
    from replay buffer and use the data to train
    the network.
    """
    FancyLogger.start_timing()
    network = NeuralNetwork(size)
    NETWORK_STORAGE.save_network(0, network)
    FancyLogger.set_network_status("Waiting for data...")
    while replay_storage.buffer.qsize() < constants.BATCH_SIZE:
        sleep(1)
        if self_play.force_quit(None):
            return

    FancyLogger.set_network_status("Starting training...")

    for i in range(iterations):
        FancyLogger.set_training_step((i+1))
        inputs, expected_out = replay_storage.sample_batch()
        loss = network.train(inputs, expected_out)
        if not i % constants.SAVE_CHECKPOINT:
            network_storage.save_network(i, network)
        FancyLogger.set_network_status("Training loss: {}".format(loss))
        #Graph.plot_data("Training Evaluation", None, loss[0])
        if self_play.force_quit(None):
            break
    network_storage.save_network(iterations, network)
    FancyLogger.set_network_status("Training finished!")

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
                copy_game = self_play.get_game(type(game).__name__, game.size, None, ".")
                copy_game.init_state = game.start_state()
                game = copy_game
                p1 = self_play.get_ai_algorithm(type(p1).__name__, game, ".")
                p2 = self_play.get_ai_algorithm(type(p2).__name__, game, ".")
            game_thread = Process(target=self_play.play_loop, args=(game, p1, p2, 0, gui, plot_data, network_storage, replay_storage))
            #game_thread = GameThread(game, p1, p2, gui, plot_data, network_storage, replay_storage)
            game_thread.start() # Start game logic thread.

        if network_storage is not None and constants.GAME_THREADS > 1:
            # Run the network training iterations.
            if plot_data:
                train_thread = threading.Thread(target=train_network,
                                                args=(network_storage, game.size,
                                                      replay_storage, constants.TRAINING_STEPS))
                train_thread.start()
            else:
                train_network(network_storage, game.size, replay_storage, constants.TRAINING_STEPS)

        if plot_data:
            Graph.run(gui, "Training Evaluation", "Training Iteration", "Winrate") # Start graph window in main thread.
        if gui is not None:
            gui.run() # Start GUI on main thread.
    else:
        self_play.play_loop(game, p1, p2, 0, network_storage=network_storage, replay_storage=replay_storage)

def save_models(model, path):
    print("Saving model to file: {}".format(path), flush=True)
    pickle.dump(model, open(path, "wb"))

def load_model(path):
    print("Loading model from file: {}".format(path), flush=True)
    return pickle.load(open(path, "rb"))

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

game = self_play.get_game(game_name, board_size, rand_seed, wildcard)
p_white = self_play.get_ai_algorithm(player1, game, wildcard)
p_black = self_play.get_ai_algorithm(player2, game, wildcard)

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
    queue = Queue(constants.TRAINING_STEPS // constants.SAVE_CHECKPOINT)
    NETWORK_STORAGE = NetworkStorage(queue)
    REPLAY_STORAGE = ReplayStorage()
    if constants.RANDOM_INITIAL_GAMES:
        if type(p_white).__name__ == "MCTS":
            p_white = self_play.get_ai_algorithm("Random", game, ".")
        if type(p_black).__name__ == "MCTS":
            p_black = self_play.get_ai_algorithm("Random", game, ".")

if __name__ == "__main__":
    prepare_training(game, p_white, p_black,
                     gui=gui,
                     plot_data="-p" in options,
                     network_storage=NETWORK_STORAGE,
                     replay_storage=REPLAY_STORAGE)
