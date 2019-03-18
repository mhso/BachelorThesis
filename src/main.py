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
    from numpy import array
    from controller.latrunculi import Latrunculi
    from controller import self_play
    from model.storage import ReplayStorage, NetworkStorage
    from model.neural import NeuralNetwork, DummyNetwork
    from view.log import FancyLogger
    from view.visualize import Gui
    from view.graph import GraphHandler
    import constants
    import sys
    import os

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
            network_storage.save_network_to_file(iteration, network, GAME_NAME)
        if "-ds" in argv:
            network_storage.save_network_to_sql(network)
        if "-s" in argv or "-ds" in argv:
            save_loss(loss[0], iteration)
    FancyLogger.set_network_status("Training loss: {}".format(loss[0]))
    GraphHandler.plot_data("Training Loss", "Training Loss", iteration+1, loss[0])

def show_performance_data(ai, index, step, data):
    # Get result of eval against minimax.
    avg_data = sum(data) / len(data)
    values = [None, None, None]
    values[index] = avg_data
    FancyLogger.set_performance_values(values)
    GraphHandler.plot_data("Training Evaluation", ai, step, avg_data)

def handle_performance_data(step, perform_data, perform_size):
    """
    Get performance data from games against alternate AIs.
    Print/plot the results.
    """
    p1 = perform_data[0]
    p2 = perform_data[1]
    p3 = perform_data[2]
    if len(p1) >= perform_size:
        show_performance_data("Versus Minimax", 0, step, p1)
        if "-s" in argv:
            save_perform_data(perform_data[0], "minimax", step) # Save to file.
        perform_data[0] = []
    elif len(p2) >= perform_size:
        show_performance_data("Versus Random", 1, step, p2)
        if "-s" in argv:
            save_perform_data(perform_data[1], "random", step) # Save to file.
        perform_data[1] = []
    elif len(p3) >= perform_size:
        show_performance_data("Versus MCTS", 2, step, p3)
        if "-s" in argv:
            save_perform_data(perform_data[2], "mcts", step) # Save to file.
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
    if not perform_started[conn]:
        # Tell the process to start running perform eval games.
        perform_started[conn] = True
        conn.send("eval_perform")
    else:
        # Nothing of note happens, indicate that process should carry on as usual.
        conn.send(None)
    if new_games >= constants.GAMES_PER_TRAINING:
        # Tell the network to train on a batch of games.
        train_network(network_storage, replay_storage, training_step)
        training_step += 1
        new_games = 0
        if training_step == constants.TRAINING_STEPS:
            FancyLogger.set_network_status("Training finished!")
            return True, new_games, training_step
        if not training_step % constants.EVAL_CHECKPOINT:
            # Indicate that the process should run performance evaluation games.
            for k in perform_started.keys():
                perform_started[k] = False
    return False, new_games, training_step

def evaluate_games(game, eval_queue, network_storage):
    """
    Evaluate a queue of games using the latest neural network.
    """
    arr = array([v for _, v in eval_queue])
    # Evaluate everything in the queue.
    policies, values = network_storage.latest_network().evaluate(arr)
    for i, c in enumerate(eval_queue):
        # Send result to all processes in the queue.
        g_name = type(game).__name__
        logits = policies[i] if g_name != "Latrunculi" else (policies[0][i], policies[1][i])
        c[0].send((logits, values[i][0]))

def load_all_perform_data():
    perf_mini = load_perform_data("minimax", None)
    if perf_mini:
        for t_step, data in perf_mini:
            show_performance_data("Versus Minimax", 0, t_step, data)
    perf_rand = load_perform_data("random", None)
    if perf_rand:
        for t_step, data in perf_rand:
            show_performance_data("Versus Random", 1, t_step, data)
    perf_mcts = load_perform_data("mcts", None)
    if perf_mcts:
        for t_step, data in perf_mcts:
            show_performance_data("Versus MCTS", 2, t_step, data)

def initialize_network(game, network_storage):
    training_step = 0
    # Construct the initial network.
    #if the -l option is selected, load a network from files
    if "-l" in argv:
        model = network_storage.load_network_from_file(None, GAME_NAME) #TODO: replace None with the argument for NN version
    elif "-dl" in argv:
        model = network_storage.load_newest_network_from_sql()

    if "-l" in argv or "-dl" in argv:
        training_step = network_storage.curr_step+1
        FancyLogger.set_training_step(training_step)
        # Load previously saved network loss + performance data.
        losses = []
        for i in range(training_step):
            losses.append(load_loss(i))
        load_all_perform_data()

        GraphHandler.plot_data("Training Loss", "Training Loss", None, losses)
        FancyLogger.start_timing()
        network = NeuralNetwork(game, model=model)
        network_storage.save_network(training_step-1, network)
        FancyLogger.set_network_status("Training loss: {}".format(losses[-1]))
    else:
        network = NeuralNetwork(game)
        network_storage.save_network(0, network)
        FancyLogger.set_network_status("Waiting for data...")
    return training_step

def monitor_games(game_conns, game, network_storage, replay_storage):
    """
    Listen for updates from self-play processes.
    These include:
        - requests for network evaluation.
        - the result of a terminated game.
        - the result of performance evaluation games.
        - logging events.
    """
    FancyLogger.start_timing()
    training_step = initialize_network(game, network_storage)
    FancyLogger.total_games = len(replay_storage.buffer)
    FancyLogger.set_game_and_size(type(game).__name__, game.size)

    # Notify processes that network is ready.
    for conn in game_conns:
        conn.send("go")

    eval_queue = []
    queue_size = constants.GAME_THREADS
    perform_data = [[], [], []]
    perform_size = constants.GAME_THREADS
    perform_started = {conn: True for conn in game_conns}
    new_games = 0

    while True:
        try:
            for conn in wait(game_conns):
                status, val = conn.recv()
                if status == "evaluate":
                    # Process has data that needs to be evaluated. Add it to the queue.
                    eval_queue.append((conn, val))
                    if len(eval_queue) == queue_size:
                        evaluate_games(game, eval_queue, network_storage)
                        eval_queue = []
                elif status == "game_over":
                    FancyLogger.increment_total_games()
                    replay_storage.save_game(val)
                    if "-s" in argv:
                        replay_storage.save_replay(val, training_step, GAME_NAME)
                    if "-ds" in argv:
                        replay_storage.save_game_to_sql(val)
                    new_games += 1
                    finished, new_games, training_step = game_over(conn, training_step, new_games,
                                                                   perform_started, replay_storage,
                                                                   network_storage)
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

                    handle_performance_data(training_step, perform_data, perform_size)
        except KeyboardInterrupt:
            for conn in game_conns:
                conn.close()
            print("Exiting...")
            return
        except EOFError as e:
            print(e)
            return

def prepare_training(game, p1, p2, **kwargs):
    # Extract arguments.
    gui = kwargs.get("gui", None)
    plot_data = kwargs.get("plot_data", False)
    network_storage = kwargs.get("network_storage", None)
    replay_storage = kwargs.get("replay_storage", None)

    if gui is not None or plot_data or self_play.is_mcts(p1) or self_play.is_mcts(p2):
        # If GUI is used, if a non-human is playing, or if
        # several games are being played in parallel,
        # create seperate thread(s) to run the AI game logic in.
        if constants.GAME_THREADS > 1:
            # Don't use plot/GUI if several games are played.
            gui = None
        pipes = []
        for i in range(constants.GAME_THREADS):
            if i > 0: # Make copies of game and players.
                game = self_play.get_game(type(game).__name__, game.size, "random", ".")
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

        #if "-l" option is selected load old replays from file
        #else if "-ld" option is selected load old replays sql database
        if "-l" in argv:
            replay_storage.load_replay(None, GAME_NAME) #TODO: replace None with the argument for NN version
        elif "-dl" in argv:
            replay_storage.load_games_from_sql()

        if pipes != []:
            # Start monitor thread.
            monitor = Thread(target=monitor_games, args=(pipes, game, network_storage, replay_storage))
            monitor.start()

        if plot_data:
            graph_1 = GraphHandler.new_graph("Training Loss", gui, "Training Iteration", "Loss", gui is None) # Start graph window in main thread.
            graph_2 = GraphHandler.new_graph("Training Evaluation", graph_1, "Training Iteration", "Winrate", gui is None) # Start graph window in main thread.
            if gui is None:
                graph_2.run("top-r")
        if gui is not None:
            gui.run() # Start GUI on main thread.
    else:
        self_play.play_loop(game, p1, p2, 0)

def save_perform_data(data, ai, step):
    location = "../resources/" + GAME_NAME + "/misc/"
    filename = "perform_eval_{}_{}.bin".format(ai, step)

    if not os.path.exists((location)):
            os.makedirs((location))

    pickle.dump(data, open(location + filename, "wb"))

def save_loss(loss, step):
    location = "../resources/" + GAME_NAME + "/misc/"
    filename = "loss_{}.bin".format(step)

    if not os.path.exists((location)):
            os.makedirs((location))

    pickle.dump(loss, open(location + filename, "wb"))

def load_perform_data(ai, step):
    try:
        data = None
        path = "../resources/" + GAME_NAME + "/misc/perform_eval_"
        if step:
            data = pickle.load(open("{}{}_{}.bin".format(path, ai, step), "rb"))
        else:
            data = []
            files = glob("{}{}_*".format(path, ai))
            if files == []:
                return None
            for f in files:
                step = f.split("_")[-1][:-4]
                data.append((int(step), pickle.load(open(f, "rb"))))
            data.sort(key=lambda sd: sd[0])
        return data
    except IOError:
        return None

def load_loss(step):
    """
    Loads network training loss for given training step.
    If no such data exists, returns 1.
    """

    try:
        loss = pickle.load(open("../resources/" + GAME_NAME + "/misc/loss_{}.bin".format(step), "rb"))
        return loss
    except IOError:
        return 1

def invalid_args(args, options, wildcard):
    if ("MCTS" in args or len(args) - len(options) == 1
             or args[0] == wildcard or args[1] == wildcard):
        if "-g" in options:
            return "Can't use GUI during MCTS/NN training"
        if "Human" in args:
            return "Can't play as human during MCTS/NN training"
    elif "-l" in args or "-s" in args:
        return "Can't save/load models or games when not training"
    return None

if __name__ == "__main__":
    # Load arguments for running the program.
    # The args, in order, correspond to the variables below.
    WILDCARD = "."
    PLAYER_1 = WILDCARD
    PLAYER_2 = WILDCARD
    GAME_NAME = WILDCARD
    BOARD_SIZE = constants.DEFAULT_BOARD_SIZE
    RAND_SEED = "random"

    OPTION_LIST = ["-s", "-l", "-v", "-t", "-g", "-p", "-ds", "-dl"]
    options = []
    args = []
    # Seperate arguments from options.
    for s in argv:
        if s in OPTION_LIST:
            options.append(s)
        else:
            args.append(s)

    ARGS_ERROR = invalid_args(argv, options, WILDCARD)
    if ARGS_ERROR:
        print(f"Error: conflicting arguments. {ARGS_ERROR}.")
        exit(0)

    argc = len(args)
    if argc > 1:
        if args[1] in ("-help", "-h"):
            print("Usage: {} [player1] [player2] [game] [board_size] [rand_seed] [<options>]".format(args[0]))
            print("Write '{}' in place of any argument to use default value".format(WILDCARD))
            print("Options: -v (verbose), -t (time operations), -s (save models), -l (load models), -g (use GUI), -p (plot data)")
            print("Fx. 'python {} Minimax MCTS Latrunculi . 42 -g'".format(args[0]))
            exit(0)
        PLAYER_1 = args[1] # Algorithm playing as player 1.

        if argc == 2 or argc == 3:
            GAME = Latrunculi(BOARD_SIZE)
            if argc == 2: # If only one player is given, player 2 will be the same algorithm.
                PLAYER_2 = PLAYER_1
        if argc > 2:
            PLAYER_2 = args[2] # Algorithm playing as player 2.

            if argc > 3:
                GAME_NAME = args[3] # Game to play.
                if argc > 4:
                    if args[4] != WILDCARD:
                        BOARD_SIZE = int(args[4]) # Size of board.

                    if argc > 5 and args[5] != WILDCARD:
                        if args[5] != "random":
                            RAND_SEED = int(args[5])
                        else:
                            RAND_SEED = args[5] # Use numpy-determined random seed.

    GAME = self_play.get_game(GAME_NAME, BOARD_SIZE, RAND_SEED, WILDCARD)
    P_WHITE = self_play.get_ai_algorithm(PLAYER_1, GAME, WILDCARD)
    P_BLACK = self_play.get_ai_algorithm(PLAYER_2, GAME, WILDCARD)

    print("Playing '{}' with board size {}x{} with '{}' vs. '{}'".format(
        type(GAME).__name__, BOARD_SIZE, BOARD_SIZE, type(P_WHITE).__name__, type(P_BLACK).__name__), flush=True)
    PLAYER_1 = PLAYER_1.lower()
    PLAYER_2 = PLAYER_2.lower()

    gui = None
    if "-g" in options or PLAYER_1 == "human" or PLAYER_2 == "human":
        gui = Gui(GAME)
        GAME.register_observer(gui)
        if PLAYER_1 == "human":
            P_WHITE.gui = gui
        if PLAYER_2 == "human":
            P_BLACK.gui = gui

    NETWORK_STORAGE = None
    REPLAY_STORAGE = None
    if self_play.is_mcts(P_WHITE) or self_play.is_mcts(P_BLACK):
        NETWORK_STORAGE = NetworkStorage()
        REPLAY_STORAGE = ReplayStorage()

        """
        if "-dl" in options:
            REPLAY_STORAGE.load_game_from_sql()
            sys.exit("test")
        """

        if constants.RANDOM_INITIAL_GAMES:
            if self_play.is_mcts(P_WHITE):
                P_WHITE = self_play.get_ai_algorithm("Random", GAME, ".")
            if self_play.is_mcts(P_BLACK):
                P_BLACK = self_play.get_ai_algorithm("Random", GAME, ".")
    elif constants.GAME_THREADS > 1:
        # If we are not playing with MCTS,
        # disable multi-threading.
        constants.GAME_THREADS = 1

    print("Main PID: {}".format(getpid()))
    prepare_training(GAME, P_WHITE, P_BLACK,
                     gui=gui,
                     plot_data="-p" in options,
                     network_storage=NETWORK_STORAGE,
                     replay_storage=REPLAY_STORAGE)
