"""
----------------------------------------
main: Run game iterations and do things.
----------------------------------------
"""
if __name__ == "__main__":
    # This atrocious if statement is needed since these imports would
    # otherwise be run everytime we start a new process (no bueno).
    import pickle
    from threading import Thread
    from multiprocessing import Process, Pipe
    from multiprocessing.connection import wait
    from os import getpid
    from glob import glob
    from sys import argv
    from time import sleep
    from numpy import array
    from controller.latrunculi import Latrunculi
    from controller import self_play
    from model.storage import ReplayStorage, NetworkStorage
    from model.neural import NeuralNetwork, DummyNetwork
    from view.log import FancyLogger
    from view.visualize import Gui
    from view.graph import Graph
    import constants

def construct_network(size):
    FancyLogger.start_timing()
    network = NeuralNetwork(size)
    FancyLogger.set_network_status("Waiting for data...")
    return network

def train_network(network_storage, replay_storage, iteration):
    """
    Trains the network by sampling a batch of data
    from replay buffer.
    """
    network = network_storage.latest_network()
    FancyLogger.set_network_status("Training...")

    FancyLogger.set_training_step((iteration+1))
    inputs, expected_out = replay_storage.sample_batch()
    loss = network.train(inputs, expected_out)
    if not iteration % constants.SAVE_CHECKPOINT:
        network_storage.save_network(iteration, network)
        if "-s" in argv:
            network_storage.save_network_to_file(iteration, network)
    FancyLogger.set_network_status("Training loss: {}".format(loss))
    #Graph.plot_data("Training Evaluation", None, loss[0])

def show_performance_data(step, perform_data, perform_size):
    """
    Get performance data from games against alternate AIs.
    Print/plot the results.
    """
    p1 = perform_data[0]
    p2 = perform_data[1]
    p3 = perform_data[2]
    if len(p1) >= perform_size:
        # Get result of eval against minimax.
        avg_mini = sum(p1) / len(p1)
        FancyLogger.set_performance_values([avg_mini, None, None])
        Graph.plot_data("Versus Minimax", step, avg_mini)
        perform_data[0] = []
    elif len(p2) >= perform_size:
        # Get result of eval against random.
        avg_rand = sum(p2) / len(p2)
        FancyLogger.set_performance_values([None, avg_rand, None])
        Graph.plot_data("Versus Random", step, avg_rand)
        perform_data[1] = []
    elif len(p3) >= perform_size:
        # Get result of eval against basic mcts.
        avg_mcts = sum(p3) / len(p3)
        FancyLogger.set_performance_values([None, None, avg_mcts])
        Graph.plot_data("Versus MCTS", step, avg_mcts)
        perform_data[2] = []

def game_over(conn, training_step, new_games, perform_started, replay_storage, network_storage):
    """
    Handle cases for when a game is completed on a process.
    These include:
        - Train the network if a big enough batch size is ready.
        - Start evaluating performance of MCTS against alternate AI's.
        - Check if training is finished.
    @returns True or false, indicating whether training is complete.
    """
    if new_games >= constants.BATCH_SIZE:
        # Tell the network to train on a batch of games.
        train_network(network_storage, replay_storage, training_step)
        training_step += 1
        new_games = 0
        if training_step == constants.TRAINING_STEPS:
            FancyLogger.set_network_status("Training finished!")
            return True
        if not training_step % constants.EVAL_CHECKPOINT:
            # Indicate that the process should run performance evaluation games.
            for k in perform_started.keys():
                perform_started[k] = False
    elif not perform_started[conn]:
        # Tell the process to start running perform eval games.
        perform_started[conn] = True
        conn.send("eval_perform")
    else:
        # Nothing of note happens, indicate that process should carry on as usual.
        conn.send(None)
    return False

def evaluate_games(eval_queue, network_storage):
    """
    Evaluate a queue of games using the latest neural network.
    """
    arr = array([v for _, v in eval_queue])
    # Evaluate everything in the queue.
    policies, values = network_storage.latest_network().evaluate(arr)
    for i, c in enumerate(eval_queue):
        # Send result to all processes in the queue.
        c[0].send(((policies[0][i], policies[1][i]), values[i]))

def monitor_games(game_conns, network_storage, replay_storage):
    """
    Listen for updates from self-play processes.
    These include:
        - requests for network evaluation.
        - the result of a terminated game.
        - the result of performance evaluation games.
        - logging events.
    """
    while network_storage.networks == {}:
        # Wait for network to be constructed/compiled.
        sleep(0.5)

    # Notify processes that network is ready.
    for conn in game_conns:
        conn.send("go")

    eval_queue = []
    queue_size = constants.GAME_THREADS
    perform_data = [[], [], []]
    perform_size = constants.EVAL_ITERATIONS * constants.GAME_THREADS
    perform_started = {conn: True for conn in game_conns}
    training_step = 0
    new_games = 0

    while True:
        try:
            for conn in wait(game_conns):
                status, val = conn.recv()
                if status == "evaluate":
                    # Process has data that needs to be evaluated. Add it to the queue.
                    eval_queue.append((conn, val))
                    if len(eval_queue) == queue_size:
                        evaluate_games(eval_queue, network_storage)
                        eval_queue = []
                elif status == "game_over":
                    replay_storage.save_game(val)
                    if "-s" in argv:
                        replay_storage.save_replay(val, training_step)
                    new_games += 1
                    finished = game_over(conn, training_step, new_games,
                                         perform_started, replay_storage, network_storage)
                    if finished:
                        for c in game_conns:
                            c.close()
                        return
                elif status == "log":
                    FancyLogger.set_thread_status(val[1], val[0])
                elif status[:7] == "perform":
                    # Get performance data from games against alternate AIs.
                    if status == "perform_mini":
                        perform_data[0].append(val)
                    elif status == "perform_rand":
                        perform_data[1].append(val)
                    elif status == "perform_mcts":
                        perform_data[2].append(val)
                    step = network_storage.curr_step

                    show_performance_data(step, perform_data, perform_size)
        except EOFError:
            pass

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
        pipes = []
        for i in range(constants.GAME_THREADS):
            if i > 0: # Make copies of game and players.
                copy_game = self_play.get_game(type(game).__name__, game.size, None, ".")
                copy_game.init_state = game.start_state()
                game = copy_game
                p1 = self_play.get_ai_algorithm(type(p1).__name__, game, ".")
                p2 = self_play.get_ai_algorithm(type(p2).__name__, game, ".")
            parent, child = Pipe()
            pipes.append(parent)

            if gui is None:
                #self_play.spawn_process(game, p1, p2, gui, plot_data, child)
                game_thread = Process(target=self_play.play_loop,
                                      args=(game, p1, p2, 0, gui, plot_data, child))
            else:
                pipes = []
                game_thread = Thread(target=self_play.play_loop,
                                     args=(game, p1, p2, 0, gui, plot_data, None))
            game_thread.start() # Start game logic thread.

        if pipes != []:
            # Start monitor thread.
            monitor = Thread(target=monitor_games, args=(pipes, network_storage, replay_storage))
            monitor.start()

        if network_storage is not None and constants.GAME_THREADS > 1:
            # Construct the initial network.
            network = construct_network(game.size)
            network_storage.save_network(0, network)

        if plot_data:
            Graph.run(gui, "Training Evaluation", "Training Iteration", "Winrate") # Start graph window in main thread.
        if gui is not None:
            gui.run() # Start GUI on main thread.
    else:
        self_play.play_loop(game, p1, p2, 0)

def save_models(model, path):
    print("Saving model to file: {}".format(path), flush=True)
    pickle.dump(model, open(path, "wb"))

def load_model(path):
    print("Loading model from file: {}".format(path), flush=True)
    return pickle.load(open(path, "rb"))

if __name__ == "__main__":
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
        NETWORK_STORAGE = NetworkStorage()
        REPLAY_STORAGE = ReplayStorage()
        if constants.RANDOM_INITIAL_GAMES:
            if type(p_white).__name__ == "MCTS":
                p_white = self_play.get_ai_algorithm("Random", game, ".")
            if type(p_black).__name__ == "MCTS":
                p_black = self_play.get_ai_algorithm("Random", game, ".")
    elif constants.GAME_THREADS > 1:
        # If we are not playing with MCTS,
        # disable multi-threading.
        constants.GAME_THREADS = 1

    print("Main PID: {}".format(getpid()))
    prepare_training(game, p_white, p_black,
                     gui=gui,
                     plot_data="-p" in options,
                     network_storage=NETWORK_STORAGE,
                     replay_storage=REPLAY_STORAGE)
