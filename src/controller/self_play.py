"""
----------------------------------------------------------------
self_play: Run game iterations, with any combination of players.
May be run in a seperate process.
----------------------------------------------------------------
"""
from sys import argv
from time import time, sleep
from multiprocessing import current_process
from config import Config
from view.log import log
from view.graph import GraphHandler

def force_quit(gui):
    return gui is not None and not gui.active or GraphHandler.closed()

def is_mcts(ai):
    return type(ai).__name__ == "MCTS"

def getpid():
    return current_process().name

def play_game(game, player_white, player_black, config, gui=None, connection=None):
    """
    Play a game to the end, and return the resulting state.
    """
    state = game.start_state()
    counter = 0
    time_game = time()
    if gui is not None:
        sleep(1)
        gui.update(state) # Update GUI, to clear board, if several games are played sequentially.
    while not game.terminal_test(state) and counter < config.LATRUNCULI_MAX_MOVES:
        time_turn = time()

        if game.player(state):
            state = player_white.execute_action(state)
        else:
            state = player_black.execute_action(state)

        game.history.append(state)

        pieces = state.count_pieces()
        log("Num of pieces, White: {} Black: {}".format(pieces[0], pieces[1]))
        if connection:
            turn_took = '{0:.3f}'.format((time() - time_turn))
            p_1, p_2 = (player_black, player_white) if state.player else (player_white, player_black)
            p_1_name, p_2_name = type(p_1).__name__, type(p_2).__name__
            thread_status = (f"Moves: {align_with_spacing(len(game.history), 3)}." +
                             f" {p_2_name} ({state.str_player()})'s turn, " +
                             f"w: {align_with_spacing(pieces[0],2)}, " +
                             f"b: {align_with_spacing(pieces[1],2)}. Turn took {turn_took} s.")
            if p_1_name == "MCTS":
                thread_status += f" Q: {p_1.chosen_node.q_value:.5f}."
            if p_1_name != "MCTS" or p_2_name != "MCTS":
                thread_status += " - Eval vs. {}".format(p_1_name if p_2_name == "MCTS" else p_2_name)
            connection.send(("log", [thread_status, getpid()]))
        elif "-t" in argv:
            turn_took = '{0:.3f}'.format((time() - time_turn))
            print(f"Turn took {turn_took} s")

        if force_quit(gui):
            print("{}: Forcing exit...".format(getpid()))
            exit(0)

        if gui is not None:
            if type(player_white).__name__ != "Human" and not state.player:
                sleep(config.GUI_AI_SLEEP)
            elif type(player_black).__name__ != "Human" and state.player:
                sleep(config.GUI_AI_SLEEP)
            gui.update(state)
        counter += 1

    util = game.utility(state, True)
    winner = "White" if util == 1 else "Black" if util else "Draw"
    log("Game over! Winner: {}".format(winner))
    if "-t" in argv:
        print("Game took: {0:.3f} s".format(time() - time_game))
    if connection:
        connection.send(("log", ["Game over! Winner: {}, util: {}".format(winner, util), getpid()]))

    # Return resulting state of game.
    return state

def align_with_spacing(number, total_lenght):
    """
    Used for adding spaces before the 'number',
    so that the total length of the return string matches 'total_length'.
    """
    val = ""
    for _ in range(len(str(number)), total_lenght):
        val += " "
    return "{}{}".format(val, str(number))

def evaluate_against_ai(game, player1, player2, mcts_player, num_games, config, connection=None):
    """
    Evaluate MCTS/NN model against a given AI algorithm.
    Plays out a given number of games and returns
    the ratio of games won by MCTS in the range
    -1 to 1, -1 meaning losing all games, 0 meaning
    all games were draws and 1 being winning all games.
    """
    wins = 0
    for _ in range(num_games):
        result = play_game(game, player1, player2, config, connection=connection)
        wins += game.utility(result, mcts_player)
        game.reset()
    return wins/num_games # Return ratio of games won.

def minimax_for_game(game):
    game_name = type(game).__name__
    if game_name == "Latrunculi":
        return "Minimax"
    if game_name == "Connect_Four":
        return "Minimax_CF"
    if game_name == "Othello":
        return "Minimax_Othello"
    return "unknown"

def evaluate_model(game, player, config, status, connection):
    """
    Evaluate MCTS/NN model against three different AI
    algorithms. Print/plot result of evaluation.
    """
    num_games = config.EVAL_GAMES // config.EVAL_PROCESSES
    num_sample_moves = player.cfg.NUM_SAMPLING_MOVES
    player.cfg.NUM_SAMPLING_MOVES = 0 # Disable softmax sampling during evaluation.
    play_as_white = status[1] == 1

    if not status[0]:
        connection.send(("log", ["Evaluating against Random", getpid()]))
        p_1, p_2 = player, get_ai_algorithm("Random", game, ".")
        if not play_as_white:
            # MCTS should play as player 2.
            p_1, p_2 = p_2, p_1

        eval_random = evaluate_against_ai(game, p_1, p_2, play_as_white,
                                          num_games, config, connection)

        connection.send((f"perform_rand_{status[1]}", eval_random))
    else:
        # If we have a good winrate against random,
        # we additionally evaluate against better AIs.
        connection.send(("log", ["Evaluating against Minimax", getpid()]))
        p_1, p_2 = player, get_ai_algorithm("Minimax", game, ".")
        if not play_as_white:
            # MCTS should play as player 2.
            p_1, p_2 = p_2, p_1

        eval_minimax = evaluate_against_ai(game, p_1, p_2, play_as_white,
                                           num_games, config, connection)

        connection.send((f"perform_mini_{status[1]}", eval_minimax))

        connection.send(("log", ["Evaluating against basic MCTS", getpid()]))
        p_1, p_2 = player, get_ai_algorithm("MCTS_Basic", game, ".")
        if not play_as_white:
            # MCTS should play as player 2.
            p_1, p_2 = p_2, p_1

        eval_mcts = evaluate_against_ai(game, p_1, p_2, play_as_white,
                                        num_games, config, connection)

        connection.send((f"perform_mcts_{status[1]}", eval_mcts))
    player.cfg.NUM_SAMPLING_MOVES = num_sample_moves # Restore softmax sampling.

def get_game(game_name, size, rand_seed, wildcard="."):
    lower = game_name.lower()
    if lower == wildcard:
        game_name = Config.DEFAULT_GAME
        lower = game_name.lower()
    try:
        module = __import__("controller.{}".format(lower), fromlist=["{}".format(game_name)])
        algo_class = getattr(module, "{}".format(game_name))
        return algo_class(size, rand_seed)
    except ImportError:
        print("Unknown game, name must equal name of game class.")
        return None, "unknown"

def get_ai_algorithm(algorithm, game, wildcard="."):
    if algorithm == "Minimax":
        algorithm = minimax_for_game(game)
    lower = algorithm.lower()
    if lower == wildcard:
        algorithm = Config.DEFAULT_AI
        lower = algorithm.lower()
    try:
        module = __import__("controller.{}".format(lower), fromlist=["{}".format(algorithm)])
        algo_class = getattr(module, "{}".format(algorithm))
        return algo_class(game)
    except ImportError:
        print("Unknown AI algorithm, name must equal name of AI class.")
        return None, "unknown"

def play_loop(game, p1, p2, iteration, gui=None, plot_data=False, config=None, connection=None):
    """
    Run a given number of game iterations with a given AI.
    """
    cfg = config
    if not cfg:
        cfg = Config()
    if iteration == 0 and connection:
        # Wait for initial construction/compilation of network.
        if is_mcts(p1):
            p1.connection = connection
            p1.set_config(cfg)
        if is_mcts(p2):
            p2.connection = connection
            p2.set_config(cfg)
        connection.recv()
    if iteration == cfg.GAME_ITERATIONS:
        print("{} is done with training!".format(getpid()))
        return
    try:
        play_game(game, p1, p2, cfg, gui, connection)

        if connection and not gui:
            # Save game to be used for neural network training.
            connection.send(("game_over", game.clone()))
            game.__init__(game.size, "random")

        game.reset() # Reset game history.
        try:
            if is_mcts(p1) and connection and not gui:
                status = connection.recv()
                if status is not None:
                    # Evaluate performance of trained model against other AIs.
                    evaluate_model(game, p1, cfg, status, connection)
            play_loop(game, p1, p2, iteration+1, gui, plot_data, cfg, connection)
        except EOFError:
            print("f{getpid()}: Monitor process has exited... This is probably fine.")
            exit(0)
    except KeyboardInterrupt:
        if gui is not None:
            gui.close()
        if plot_data:
            GraphHandler.close_graphs()
        exit(0)


