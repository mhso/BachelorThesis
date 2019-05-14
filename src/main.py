"""
----------------------------------------------
main: Extract arguments and initialize things.
----------------------------------------------
"""
if __name__ == "__main__":
    # This atrocious if statement is needed since these imports would
    # otherwise be run everytime we start a new process (no bueno).
    import os
    from threading import Thread
    from multiprocessing import Process, Pipe
    from sys import argv
    from controller.latrunculi import Latrunculi
    from controller import self_play
    from controller.training import monitor_games, parse_load_step
    from model.storage import ReplayStorage, NetworkStorage
    from view.visualize import Gui
    from view.graph import GraphHandler
    from config import Config, set_game_specific_values

def initialize(game, p1, p2, **kwargs):
    """
    This method starts the play-loop,
    createds any GUI/graphs,
    spawns self-play actors/processes,
    starts monitor thread for MCTS self-play,
    and loads models/games from file, if these things are enabled.
    """
    # Extract arguments.
    gui = kwargs.get("gui", None)
    plot_data = kwargs.get("plot_data", False)
    network_storage = kwargs.get("network_storage", None)
    replay_storage = kwargs.get("replay_storage", None)
    config = kwargs.get("config", None)
    game_name = type(game).__name__

    if gui is not None or plot_data or self_play.is_mcts(p1) or self_play.is_mcts(p2):
        # Set whether program is running in 'test' mode, or actively training.
        test_mode = not self_play.is_mcts(p1) or not self_play.is_mcts(p2) or gui is not None
        # If GUI is used, if a non-human is playing, or if
        # several games are being played in parallel,
        # create seperate thread(s) to run the AI game logic in.
        if Config.GAME_THREADS > 1:
            # Don't use plot/GUI if several games are played.
            gui = None
        pipes = []
        games, p1s, p2s = self_play.copy_games_and_players(game, p1, p2, Config.GAME_THREADS)
        for i in range(Config.GAME_THREADS):
            child = None
            if self_play.is_mcts(p1) or self_play.is_mcts(p2):
                parent, child = Pipe()
                pipes.append(parent)

            if gui is None:
                game_thread = Process(target=self_play.init_self_play,
                                      name=f"Process {(i+1):02d}",
                                      args=(games[i], p1s[i], p2s[i], child, gui, config))
            else:
                game_thread = Thread(target=self_play.init_self_play,
                                     args=(games[i], p1s[i], p2s[i], child, gui, config))
            game_thread.start() # Start game logic thread.

        #if "-l" option is selected load old replays from file
        #else if "-ld" option is selected load old replays sql database
        if "-l" in argv or "-lg" in argv and not test_mode:
            step = parse_load_step(argv)
            replay_storage.load_replay(step, game_name)
        elif "-dl" in argv:
            replay_storage.load_games_from_sql()
        if "-s" in argv:
            location = f"../resources/{game_name}/"
            if not os.path.exists(location):
                os.makedirs((location))
                try:
                    cfg_file = open("../resources/config.txt", "r").readlines()
                    open(location+"config.txt", "w").writelines(cfg_file)
                except IOError:
                    print("Error when copying cfg file.")

        if pipes != []:
            
            # Start monitor thread.
            monitor = Thread(target=monitor_games,
                             args=(pipes, game, network_storage,
                                   replay_storage, test_mode))
            monitor.start()

        if gui is not None:
            gui.run() # Start GUI on main thread.
        elif plot_data:
            graph_1 = GraphHandler.new_graph("Policy Loss", game_name, gui, "Training Iteration", "Loss") # Start graph window in main thread.
            graph_2 = GraphHandler.new_graph("Value Loss", game_name, graph_1, "Training Iteration", "Loss") # Start graph window in main thread.
            graph_3 = GraphHandler.new_graph("Average Loss", game_name, graph_2, "Training Iteration", "Loss") # Start graph window in main thread.
            graph_4 = GraphHandler.new_graph("Training Evaluation", game_name, graph_3, "Training Iteration", "Winrate") # Start graph window in main thread.
            if gui is None:
                graph_4.run()
    else:
        self_play.play_loop(game, p1, p2, 0)

def invalid_args(args, options, wildcard):
    return False

if __name__ == "__main__":
    # Load Config from file if present.
    cfg = Config
    if "-c" in argv:
        cfg = Config.from_file("../resources/Config.txt")

    # Load arguments for running the program.
    # The args, in order, correspond to the variables below.
    WILDCARD = "."
    PLAYER_1 = WILDCARD
    PLAYER_2 = WILDCARD
    GAME_NAME = WILDCARD
    BOARD_SIZE = Config.DEFAULT_BOARD_SIZE
    RAND_SEED = "random"

    OPTION_LIST = ["-s", "-l", "-lg", "-ln", "-v", "-t", "-c", "-g", "-p", "-ds", "-dl"]
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
            print(f"Default values: '{Config.DEFAULT_AI}', '{Config.DEFAULT_AI}', "+
                  f"'{Config.DEFAULT_GAME}', '{Config.DEFAULT_BOARD_SIZE}', 'random'")
            print(f"Options: {OPTION_LIST}")
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
    set_game_specific_values(cfg, GAME)
    P_WHITE = self_play.get_ai_algorithm(PLAYER_1, GAME, WILDCARD)
    P_BLACK = self_play.get_ai_algorithm(PLAYER_2, GAME, WILDCARD)

    print("Playing '{}' with board size {}x{} with '{}' vs. '{}'".format(
        type(GAME).__name__, BOARD_SIZE, BOARD_SIZE, type(P_WHITE).__name__, type(P_BLACK).__name__), flush=True)
    PLAYER_1 = PLAYER_1.lower()
    PLAYER_2 = PLAYER_2.lower()

    gui = None
    if "-g" in options or PLAYER_1 == "human" or PLAYER_2 == "human":
        gui = Gui(GAME)
        if PLAYER_1 == "human":
            P_WHITE.gui = gui
        if PLAYER_2 == "human":
            P_BLACK.gui = gui

    NETWORK_STORAGE = None
    REPLAY_STORAGE = None
    if self_play.is_mcts(P_WHITE) or self_play.is_mcts(P_BLACK):
        NETWORK_STORAGE = NetworkStorage()
        REPLAY_STORAGE = ReplayStorage()

        if gui:
            # If GUI is active, only run with 1 process
            # and no performance evaluation.
            Config.GAME_THREADS = 1
            cfg.GAME_THREADS = 1
            Config.ACTORS = 1
            cfg.ACTORS = 1
            Config.EVAL_CHECKPOINT = {}
            cfg.EVAL_CHECKPOINT = {}
            cfg.NUM_SAMPLING_MOVES = 0
            Config.NUM_SAMPLING_MOVES = 0
            cfg.NOISE_BASE = 0
            Config.NOISE_BASE = 0
        if not self_play.is_mcts(P_WHITE) or not self_play.is_mcts(P_BLACK):
            cfg.NOISE_BASE = 0
            Config.NOISE_BASE = 0
            cfg.NUM_SAMPLING_MOVES = 0
            Config.NUM_SAMPLING_MOVES = 0
        """
        if "-dl" in options:
            REPLAY_STORAGE.load_game_from_sql()
            sys.exit("test")
        """
    elif Config.GAME_THREADS > 1:
        # If we are not playing with MCTS,
        # disable multi-threading.
        Config.ACTORS = 1
        cfg.ACTORS = 1
        Config.GAME_THREADS = 1
        cfg.GAME_THREADS = 1

    initialize(GAME, P_WHITE, P_BLACK,
               gui=gui,
               plot_data="-p" in options,
               network_storage=NETWORK_STORAGE,
               replay_storage=REPLAY_STORAGE,
               config=cfg)
