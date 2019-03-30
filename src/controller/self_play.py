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

def prepare(games):
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]

        player = player_1 if game.player(state) else player_2
        player.prepare_action(state)

def select_states(games):
    states = []
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]

        player = player_1 if game.player(state) else player_2
        player.prepare_action(state)

        states.append(player.select(state))
    return states

def play_game(games, player_white, player_black, config, gui=None, connection=None):
    """
    Play a game to the end, and return the resulting state.
    """
    active_games = [[games[i], games[i].start_state(), player_white[i], player_black[i]] for i in range(len(games))]
    counters = [0 for _ in range(len(games))]
    results = []
    time_game = time()

    while active_games:
        prepare(active_games)

        selected_states = select_states(active_games)

        for i, s in enumerate(select_states):
            active_games[i][]

        for i, data in enumerate(active_games):
            game = data[0]
            state = data[1]
            player_1 = data[2]
            player_2 = data[3]
            time_turn = time()

            if gui is not None:
                sleep(1)
                gui.update(state) # Update GUI, to clear board, if several games are played sequentially.

            if game.player(state):
                state = player_1.execute_action(state)
            else:
                state = player_2.execute_action(state)

            game.history.append(state)
            active_games[i][1] = state

            pieces = state.count_pieces()
            log("Num of pieces, White: {} Black: {}".format(pieces[0], pieces[1]))
            if connection:
                turn_took = '{0:.3f}'.format((time() - time_turn))
                p_1, p_2 = (player_2, player_1) if state.player else (player_1, player_2)
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

            counters[i] = counters[i] + 1
            if game.terminal_test(state) or counters[i] > config.LATRUNCULI_MAX_MOVES:
                active_games.pop(i)

                util = game.utility(state, True)
                winner = "White" if util == 1 else "Black" if util else "Draw"
                log("Game over! Winner: {}".format(winner))
                if "-t" in argv:
                    print("Game took: {0:.3f} s".format(time() - time_game))
                if connection:
                    connection.send(("log", ["Game over! Winner: {}, util: {}".format(winner, util), getpid()]))
                results.append(state)
    return results

def align_with_spacing(number, total_lenght):
    """
    Used for adding spaces before the 'number',
    so that the total lenght of the return string matches 'total_length'.
    """
    val = ""
    for _ in range(len(str(number)), total_lenght):
        val += " "
    return "{}{}".format(val, str(number))

def evaluate_against_ai(game, player, other, num_games, config, connection=None):
    """
    Evaluate MCTS/NN model against a given AI algorithm.
    Plays out a given number of games and returns
    the ratio of games won by MCTS in the range
    -1 to 1, -1 meaning losing all games, 0 meaning
    all games were draws and 1 being winning all games.
    """
    wins = 0
    for _ in range(num_games):
        result = play_game(game, player, other, config, connection=connection)
        wins += game.utility(result, True)
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

def evaluate_model(game, player, config, eval_others, connection):
    """
    Evaluate MCTS/NN model against three different AI
    algorithms. Print/plot result of evaluation.
    """
    num_games = config.EVAL_GAMES // config.EVAL_PROCESSES
    num_sample_moves = player.cfg.NUM_SAMPLING_MOVES
    player.cfg.NUM_SAMPLING_MOVES = 0 # Disable softmax sampling during evaluation.

    if not eval_others:
        connection.send(("log", ["Evaluating against Random", getpid()]))

        eval_random = evaluate_against_ai(game, player,
                                          get_ai_algorithm("Random", game, "."),
                                          num_games, config, connection)

        connection.send(("perform_rand", eval_random))
    else:
        # If we have a good winrate against random,
        # we additionally evaluate against better AIs.
        connection.send(("log", ["Evaluating against Minimax", getpid()]))

        eval_minimax = evaluate_against_ai(game, player,
                                           get_ai_algorithm("Minimax", game, "."),
                                           num_games, config, connection)

        connection.send(("perform_mini", eval_minimax))

        connection.send(("log", ["Evaluating against basic MCTS", getpid()]))

        eval_mcts = evaluate_against_ai(game, player,
                                        get_ai_algorithm("MCTS_Basic", game, "."),
                                        num_games, config, connection)

        connection.send(("perform_mcts", eval_mcts))
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

def play_loop(games, p1s, p2s, iteration, gui=None, config=None, connection=None):
    """
    Run a given number of game iterations with a given AI.
    """
    if iteration == config.GAME_ITERATIONS:
        print("{} is done with training!".format(getpid()))
        return
    try:
        play_game(games, p1s, p2s, config, gui, connection)

        for i in range(len(games)):
            game = games[i]
            p1 = p1s[i]
            p2 = p2s[i]
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
                        evaluate_model(game, p1, config, status, connection)
            except EOFError:
                print("f{getpid()}: Monitor process has exited... This is probably fine.")
                exit(0)
        play_loop(games, p1s, p2s, iteration+1, gui, config, connection)
    except KeyboardInterrupt:
        if gui is not None:
            gui.close()
        exit(0)

def init_self_play(game, p1, p2, connection, gui=None, config=None):
    cfg = config
    if not cfg:
        cfg = Config()

    if is_mcts(p1):
        p1.connection = connection
        p1.set_config(cfg)
    if is_mcts(p2):
        p2.connection = connection
        p2.set_config(cfg)
    # Wait for initial construction/compilation of network.
    connection.recv()

    games = []
    player_1_agents = []
    player_2_agents = []
    for _ in range(Config.GAME_THREADS // 3):
        games.append(get_game(type(game).__name__, game.size, "random", "."))
        player_1 = get_ai_algorithm(type(p1).__name__, game, ".")
        player_1.connection = connection
        player_1.set_config(cfg)
        player_2 = get_ai_algorithm(type(p2).__name__, game, ".")
        player_2.connection = connection
        player_2.set_config(cfg)
        player_1_agents.append(player_1)
        player_2_agents.append(player_2)

    play_loop(games, player_1_agents, player_2_agents, 0, gui, cfg, connection)
