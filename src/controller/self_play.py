"""
----------------------------------------------------------------
self_play: Run game iterations, with any combination of players.
May be run in a seperate process.
----------------------------------------------------------------
"""
from os import getpid
from sys import argv
from time import time, sleep
from sys import argv
from multiprocessing import Process
import constants
from view.log import log, FancyLogger
from view.graph import Graph
from util.timerUtil import TimerUtil
from util.sqlUtil import SqlUtil

def force_quit(gui):
    return gui is not None and not gui.active or Graph.stop_event.is_set()

def play_game(game, player_white, player_black, gui=None, connection=None):
    """
    Play a game to the end, and return the resulting state.
    """
    state = game.start_state()
    counter = 0
    time_game = time()
    if gui is not None:
        sleep(1)
        gui.update(state) # Update GUI, to clear board, if several games are played sequentially.
    timeGame = TimerUtil()
    timeGame.start_timing()
    time_begin = timeGame.get_datetime_str()
    count_player_moves = [0,0]
    while not game.terminal_test(state) and counter < constants.LATRUNCULI_MAX_MOVES:
        num_white, num_black = state.count_pieces()
        log("Num of pieces, White: {} Black: {}".format(num_white, num_black))
        time_turn = time()

        if game.player(state):
            state = player_white.execute_action(state)
            count_player_moves[0] += 1
        else:
            state = player_black.execute_action(state)
            count_player_moves[1] += 1

        if connection:
            ai_name = type(player_white).__name__ if state.player else type(player_black).__name__
            pieces = state.count_pieces()
            thread_status = ("Moves: {}. {}'s turn ({}), ".format(len(game.history), ai_name,
                                                                  state.str_player()) +
                             "pieces: w: {}, b: {}. Turn took {} s".format(pieces[0], pieces[1],
                                                                           time() - time_turn))
            connection.send(("log", [thread_status, getpid()]))
        elif "-t" in argv:
            print("Turn took {} s".format(time() - time_turn))

        game.history.append(state)

        if force_quit(gui):
            print("{}: Forcing exit...".format(getpid()))
            exit(0)

        if gui is not None:
            if type(player_white).__name__ != "Human" and not state.player:
                sleep(constants.GUI_AI_SLEEP)
            elif type(player_black).__name__ != "Human" and state.player:
                sleep(constants.GUI_AI_SLEEP)
            gui.update(state)
        counter += 1
    timeGame.stop_timing()
    if False:
        evalUsed = "standard"
        test_name = "n/a"
        if "-eval" in argv[len(argv)-3]:
            evalUsed = argv[len(argv)-2]
            test_name = argv[len(argv)-1]
        pieces = state.count_pieces()
        row = SqlUtil.evaluation_cost_row(time_begin, timeGame.get_computer_hostname(), getpid(), test_name, "Latrunculi Eval: {}".format(evalUsed),
                                                                game.seed_used(), type(player_white).__name__, type(player_black).__name__,
                                                                int(count_player_moves[0]), int(count_player_moves[1]),
                                                                int(pieces[0]), int(pieces[1]), timeGame.time_duration())
        sql_conn = SqlUtil.connect()
        SqlUtil.evaluation_cost_insert_row(sql_conn, row)

    winner = "Black" if state.player else "White"
    if "-t" in argv:
        print("Game over! Winner: {}, time spent: {} s".format(winner, time() - time_game))

    # Return resulting state of game.
    return state

def evaluate_against_ai(game, player, other, num_games, connection=None):
    """
    Evaluate MCTS/NN model against a given AI algorithm.
    Plays out a given number of games and returns
    the ratio of games won by MCTS in the range
    -1 to 1, -1 meaning losing all games, 0 meaning
    all games were draws and 1 being winning all games.
    """
    wins = 0
    for _ in range(num_games):
        result = play_game(game, player, other, connection=connection)
        wins += game.utility(result, True)
        game.reset()
    return wins/num_games # Return ratio of games won.

def evaluate_model(game, player, connection):
    """
    Evaluate MCTS/NN model against three different AI
    algorithms. Print/plot result of evaluation.
    """
    connection.send(("log", ["Evaluating against Minimax", getpid()]))

    eval_minimax = evaluate_against_ai(game, player,
                                       get_ai_algorithm(
                                           "Minimax" if type(game).__name__ == "Latrunculi"
                                           else "Minimax_CF", game, "."),
                                       constants.EVAL_ITERATIONS, connection)

    connection.send(("perform_mini", eval_minimax))
    connection.send(("log", ["Evaluating against Random", getpid()]))

    eval_random = evaluate_against_ai(game, player,
                                      get_ai_algorithm("Random", game, "."),
                                      constants.EVAL_ITERATIONS, connection)

    connection.send(("perform_rand", eval_random))
    connection.send(("log", ["Evaluating against basic MCTS", getpid()]))

    eval_mcts = evaluate_against_ai(game, player,
                                    get_ai_algorithm("MCTS_Basic", game, "."),
                                    constants.EVAL_ITERATIONS, connection)

    connection.send(("perform_mcts", eval_mcts))

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

def play_loop(game, p1, p2, iteration, gui=None, plot_data=False, connection=None):
    """
    Run a given number of game iterations with a given AI.
    After each game iteration, if the model is MCTS,
    we save the model for later use. If 'load' is true,
    we load these MCTS models.
    """
    if iteration == 0 and connection:
        # Wait for initial construction/compilation of network.
        if type(p1).__name__ == "MCTS":
            p1.connection = connection
        if type(p2).__name__ == "MCTS":
            p2.connection = connection
        connection.recv()
    if iteration == constants.GAME_ITERATIONS:
        print("{} is done with training!".format(getpid()))
        return
    try:
        play_game(game, p1, p2, gui, connection)

        if connection:
            # Save game to be used for neural network training.
            connection.send(("game_over", game.clone()))
            #FancyLogger.increment_total_games()
            if (type(p1).__name__ == "Random" and constants.RANDOM_INITIAL_GAMES
                    and iteration >= constants.RANDOM_INITIAL_GAMES // constants.GAME_THREADS):
                # We are done with random game generation,
                # moving on to actual self-play.
                p1 = get_ai_algorithm("MCTS", game, ".")
                p1.connection = connection
                p2 = get_ai_algorithm("MCTS", game, ".")
                p2.connection = connection

        game.reset() # Reset game history.
        if type(p1).__name__ == "MCTS" and connection and connection.recv():
            # Evaluate performance of trained model against other AIs.
            evaluate_model(game, p1, connection)
        play_loop(game, p1, p2, iteration+1, gui, plot_data, connection)
    except KeyboardInterrupt:
        print("Exiting by interrupt...")
        if gui is not None:
            gui.close()
        if plot_data:
            Graph.close()
        exit(0)
