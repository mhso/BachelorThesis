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

def root_nodes(games):
    root_nodes = []
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]

        player = player_1 if game.player(state) else player_2
        root_nodes.append(player.create_root_node(state))
    return root_nodes

def select_nodes(games, roots):
    nodes = []
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        root = roots[i]

        player = player_1 if game.player(state) else player_2

        nodes.append(player.select(root))
    return nodes

def prepare_actions(games, nodes):
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        root = nodes[i]

        player = player_1 if game.player(state) else player_2

        player.prepare_action(root)

def expand_nodes(games, nodes, policies, values):
    return_values = []
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        node = nodes[i]
        policy = policies[i]

        player = player_1 if game.player(state) else player_2

        return_values.append(player.set_evaluation_data(node, policy, values[i]))
        player.expand(node, game.actions(state), policy)
    return return_values

def backprop(games, nodes, values):
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        node = nodes[i]
        value = values[i]

        player = player_1 if game.player(state) else player_2

        player.back_propagate(node, -value)

def play_as_mcts(active_games, config, connection):
    roots = root_nodes(active_games)
    # Get network evaluation from main process.
    connection.send(("evaluate", [g[0].structure_data(n.state) for (g, n) in zip(active_games, roots)]))
    policies, values = connection.recv()
    expand_nodes(active_games, roots, policies, values)
    prepare_actions(active_games, roots)

    for _ in range(config.MCTS_ITERATIONS):
        selected_nodes = select_nodes(active_games, roots)

        connection.send(("evaluate", [g[0].structure_data(n.state) for (g, n) in zip(active_games, selected_nodes)]))
        policies, values = connection.recv()
        values = expand_nodes(active_games, selected_nodes, policies, values)
        backprop(active_games, selected_nodes, values)
    return roots

def play_games(games, player_white, player_black, config, connection=None):
    """
    Play a game to the end, and return the resulting state.
    """
    active_games = [[games[i], games[i].start_state(), player_white[i], player_black[i]] for i in range(len(games))]
    total_games = len(games)
    counters = [0 for _ in games]
    results = []

    while active_games:
        player = active_games[0][2] if active_games[0][0].player(active_games[0][1]) else active_games[0][3]
        time_turn = time()
        if is_mcts(player):
            # Run MCTS simulations. Get resulting root nodes.
            roots = play_as_mcts(active_games, config, connection)

        finished_games_indexes = []
        for (i, (game, state, player_1, player_2)) in enumerate(active_games):
            player = player_1 if game.player(state) else player_2
            state = player.execute_action(roots[i] if is_mcts(player) else state)
            active_games[i][1] = state

            game.history.append(state)

            counters[i] = counters[i] + 1
            if game.terminal_test(state) or counters[i] > config.LATRUNCULI_MAX_MOVES:
                finished_games_indexes.append(i)
                results.append(state)

        turn_took = "{0:.3f}".format((time() - time_turn))
        num_active = len(active_games)
        num_moves = len(active_games[0][0].history)
        name_1, name_2 = type(active_games[0][2]).__name__, type(active_games[0][3]).__name__
        elems_removed = 0
        for i in finished_games_indexes:
            active_games.pop(i-elems_removed)
            elems_removed += 1

        num_active -= elems_removed
        if connection:
            status = (f"Moves: {num_moves}. Active games: "+
                      f"{num_active}/{total_games}. Turn took {turn_took} s")
            if name_1 != "MCTS" or name_2 != "MCTS":
                status += " - Eval vs. {}".format(name_1 if name_2 == "MCTS" else name_2)
            connection.send(("log", [status, getpid()]))
    return results

def align_with_spacing(number, total_length):
    """
    Used for adding spaces before the 'number',
    so that the total length of the return string matches 'total_length'.
    """
    val = ""
    for _ in range(len(str(number)), total_length):
        val += " "
    return "{}{}".format(val, str(number))

def evaluate_against_ai(game, player1, player2, mcts_player, num_games, config, connection):
    """
    Evaluate MCTS/NN model against a given AI algorithm.
    Plays out a given number of games and returns
    the ratio of games won by MCTS in the range
    -1 to 1, -1 meaning losing all games, 0 meaning
    all games were draws and 1 being winning all games.
    """
    wins = 0
    games, p1s, p2s = copy_games_and_players(game, player1, player2, num_games)
    for i in range(len(games)):
        player = p1s[i] if mcts_player else p2s[i]
        player.set_config(config)
    results = play_games(games, p1s, p2s, config, connection)
    for result in results:
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

def evaluate_model(game, player, status, config, connection):
    """
    Evaluate MCTS/NN model against three different AI
    algorithms. Print/plot result of evaluation.
    """
    num_games = config.EVAL_GAMES
    num_sample_moves = player.cfg.NUM_SAMPLING_MOVES
    player.cfg.NUM_SAMPLING_MOVES = 0 # Disable softmax sampling during evaluation.

    if not status:
        connection.send(("log", ["Evaluating against Random", getpid()]))
        p_1, p_2 = player, get_ai_algorithm("Random", game, ".")

        eval_rand_w = evaluate_against_ai(game, p_1, p_2, True, num_games // 2, config, connection)
        p_2, p_1 = p_1, p_2
        eval_rand_b = evaluate_against_ai(game, p_1, p_2, False, num_games // 2, config, connection)

        connection.send((f"perform_rand", (eval_rand_w, eval_rand_b)))
    else:
        # If we have a good winrate against random,
        # we additionally evaluate against better AIs.
        connection.send(("log", ["Evaluating against Minimax", getpid()]))
        p_1, p_2 = player, get_ai_algorithm("Minimax", game, ".")

        eval_mini_w = evaluate_against_ai(game, p_1, p_2, True, num_games // 2, config, connection)
        p_2, p_1 = p_1, p_2
        eval_mini_b = evaluate_against_ai(game, p_1, p_2, False, num_games // 2, config, connection)

        connection.send((f"perform_mini", (eval_mini_w, eval_mini_b)))

        connection.send(("log", ["Evaluating against basic MCTS", getpid()]))
        p_1, p_2 = player, get_ai_algorithm("MCTS_Basic", game, ".")

        eval_mcts_w = evaluate_against_ai(game, p_1, p_2, True, num_games // 2, config, connection)
        p_2, p_1 = p_1, p_2
        eval_mcts_b = evaluate_against_ai(game, p_1, p_2, False, num_games // 2, config, connection)

        connection.send((f"perform_mcts", (eval_mcts_w, eval_mcts_b)))
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
        play_games(games, p1s, p2s, config, connection)
        clones = []

        for i in range(len(games)):
            game = games[i]
            p1 = p1s[i]
            p2 = p2s[i]
            clones.append(game.clone())
            game.__init__(game.size, "random")

            game.reset() # Reset game history.
        try:
            if connection and not gui:
                connection.send(("game_over", clones))
                status = connection.recv()
                if status is not None:
                    # Evaluate performance of trained model against other AIs.
                    evaluate_model(games[0], p1s[0], status, config, connection)
        except EOFError:
            print("f{getpid()}: Monitor process has exited... This is probably fine.")
            exit(0)
        play_loop(games, p1s, p2s, iteration+1, gui, config, connection)
    except KeyboardInterrupt:
        if gui is not None:
            gui.close()
        exit(0)

def copy_games_and_players(game, p1, p2, amount):
    games = [game]
    p_1_agents = [p1]
    p_2_agents = [p2]
    for _ in range(1, amount):
        game = get_game(type(game).__name__, game.size, "random", ".")
        player_1 = get_ai_algorithm(type(p1).__name__, game, ".")
        player_2 = get_ai_algorithm(type(p2).__name__, game, ".")
        p_1_agents.append(player_1)
        p_2_agents.append(player_2)
        games.append(game)
    return games, p_1_agents, p_2_agents

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

    games, player_1_agents, player_2_agents = copy_games_and_players(game, p1, p2, cfg.GAME_THREADS // 3)
    for i in range(len(games)):
        player_1_agents[i].set_config(cfg)
        player_2_agents[i].set_config(cfg)

    play_loop(games, player_1_agents, player_2_agents, 0, gui, cfg, connection)
