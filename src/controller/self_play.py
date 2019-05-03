"""
----------------------------------------------------------------
self_play: Run game iterations, with any combination of players.
May be run in a seperate process.
----------------------------------------------------------------
"""
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

def create_roots(games):
    """
    Create root nodes for use in MCTS simulation. Takes as a parameter a list of tuples,
    containing data for each game. This data consist of: gametype, state, type of player 1 and type of player 2
    """
    root_nodes = []
    for data in games:
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]

        player = player_1 if game.player(state) else player_2
        root_nodes.append(player.create_root_node(state))
    return root_nodes

def select_nodes(games, roots):
    """
    Run 'select' in MCTS on a batch of root nodes.
    """
    nodes = []
    for i, root in enumerate(roots):
        data = games[i]
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        root = roots[i]

        player = player_1 if game.player(state) else player_2

        nodes.append(player.select(root))
    return nodes

def prepare_actions(games, nodes):
    """
    Add exploration noise and check for 'pass' action
    on a batch of nodes.
    """
    for i, data in enumerate(games):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        root = nodes[i]

        player = player_1 if game.player(state) else player_2

        player.prepare_action(root)

def expand_nodes(games, nodes, policies, values):
    """
    Expand a batch of node based on policy logits
    acquired from the neural network.
    """
    return_values = []
    for i, node in enumerate(nodes):
        data = games[i]
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        policy = policies[i]

        player = player_1 if game.player(state) else player_2
        return_values.append(player.set_evaluation_data(node, policy, values[i]))
    return return_values

def backprop_nodes(games, nodes, values):
    """
    Backpropagate values from the neural network
    to update a batch of nodes.
    """
    for i, node in enumerate(nodes):
        data = games[i]
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        value = values[i]

        player = player_1 if game.player(state) else player_2

        player.back_propagate(node, node.state.player, -value)

def pack_data_for_eval(active_games, networks, nodes):
    return [(-1 if networks is None else networks[g[0]][g[1].player],
             g[0].structure_data(n.state)) for (g, n) in zip(active_games, nodes)]

def play_as_mcts(active_games, networks, config, connection):
    """
    Play a batch of games as MCTS vs. MCTS.
    """
    roots = create_roots(active_games)

    # Get network evaluation from main process.
    data = pack_data_for_eval(active_games, networks, roots)
    connection.send(("evaluate", data))

    policies, values = connection.recv()
    log(f"Root policies:\n{policies}")
    log(f"OG root values: {values}")
    values = expand_nodes(active_games, roots, policies, values)
    prepare_actions(active_games, roots)

    for _ in range(config.MCTS_ITERATIONS):
        selected_nodes = select_nodes(active_games, roots)

        data = pack_data_for_eval(active_games, networks, selected_nodes)
        connection.send(("evaluate", data))
        policies, values = connection.recv()
        values = expand_nodes(active_games, selected_nodes, policies, values)
        backprop_nodes(active_games, selected_nodes, values)
    return roots

def play_games(games, player_white, player_black, config, network_steps=None, gui=None, connection=None):
    """
    Play a number of games to the end, and return the resulting states.
    """
    active_games = [[games[i], games[i].start_state(), player_white[i], player_black[i]] for i in range(len(games))]
    total_games = len(games)
    counters = [0 for _ in games]

    if gui is not None:
        sleep(1)
        gui.update(active_games[0][1]) # Update GUI, to clear board, if several games are played sequentially.

    while active_games:
        player = active_games[0][2] if active_games[0][0].player(active_games[0][1]) else active_games[0][3]
        time_turn = time()
        if is_mcts(player):
            # Run MCTS simulations. Get resulting root nodes.
            roots = play_as_mcts(active_games, network_steps, config, connection)

        finished_games_indexes = []
        for (i, (game, state, player_1, player_2)) in enumerate(active_games):
            player = player_1 if game.player(state) else player_2
            state = player.execute_action(roots[i] if is_mcts(player) else state) #gives a root node to the method if MCTS, else it gives a state
            active_games[i][1] = state

            if gui is not None:
                if type(player_white).__name__ != "Human" and not state.player:
                    sleep(config.GUI_AI_SLEEP)
                elif type(player_black).__name__ != "Human" and state.player:
                    sleep(config.GUI_AI_SLEEP)
                gui.update(state)

            log(state)

            counters[i] = counters[i] + 1
            if game.terminal_test(state) or counters[i] > config.LATRUNCULI_MAX_MOVES:
                finished_games_indexes.append(i)
                util = game.utility(state, True)
                game.terminal_value = util
                winner = "White" if util == 1 else "Black" if util == -1 else "Draw"
                log(f"Game over! Winner: {winner}")
            else:
                game.history.append(state)

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
            elif network_steps is not None:
                status += " - Eval vs Macro Networks"
            connection.send(("log", [status, getpid()]))

def align_with_spacing(number, total_length):
    """
    Used for adding spaces before the 'number',
    so that the total length of the return string matches 'total_length'.
    """
    val = ""
    for _ in range(len(str(number)), total_length):
        val += " "
    return "{}{}".format(val, str(number))

def evaluate_against_ai(game, player1, player2, mcts_player, num_games, config, connection, step=None):
    """
    Evaluate MCTS/NN model against a given AI algorithm.
    Plays out a given number of games and returns
    the ratio of games won by MCTS in the range
    -1 to 1, -1 meaning losing all games, 0 meaning
    all games were draws and 1 being winning all games.
    """
    wins = 0
    games, p1s, p2s = copy_games_and_players(game, player1, player2, num_games)
    network_steps = {}
    for i in range(len(games)):
        if is_mcts(p1s[i]):
            p1s[i].set_config(config)
        if is_mcts(p2s[i]):
            p2s[i].set_config(config)
        if step is not None:
            # Set up which networks to target (if against macro network).
            network_steps[games[i]] = {mcts_player: -1, not mcts_player: step - (i * 100)}

    network_steps = network_steps if network_steps != {} else None

    play_games(games, p1s, p2s, config, network_steps=network_steps, connection=connection)
    for g in games:
        val = g.terminal_value
        win_v = val if mcts_player or val == 0 else -val
        wins += win_v
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

def evaluate_model(game, player, step, config, connection):
    """
    Evaluate MCTS/NN model against three different AI
    algorithms. Print/plot result of evaluation.
    """
    num_games = config.EVAL_GAMES
    num_sample_moves = player.cfg.NUM_SAMPLING_MOVES
    noise_base = player.cfg.NOISE_BASE
    player.cfg.NUM_SAMPLING_MOVES = 0 # Disable softmax sampling during evaluation.
    player.cfg.NOISE_BASE = 0 # Disable noise during evaluation.
    """
    connection.send(("log", ["Evaluating against Random", getpid()]))
    rand_ai = get_ai_algorithm("Random", game, ".")

    eval_rand_w = evaluate_against_ai(game, player, rand_ai, True, num_games // 2, config, connection)
    eval_rand_b = evaluate_against_ai(game, rand_ai, player, False, num_games // 2, config, connection)

    connection.send((f"perform_rand", (eval_rand_w, eval_rand_b)))
    """
    if step > 100:
        # If we have a good winrate against random,
        # we additionally evaluate against better AIs.
        """
        connection.send(("log", ["Evaluating against Minimax", getpid()]))
        mini_ai = get_ai_algorithm("Minimax", game, ".")

        eval_mini_w = evaluate_against_ai(game, player, mini_ai, True, num_games // 2, config, connection)
        eval_mini_b = evaluate_against_ai(game, mini_ai, player, False, num_games // 2, config, connection)

        connection.send((f"perform_mini", (eval_mini_w, eval_mini_b)))
        connection.send(("log", ["Evaluating against basic MCTS", getpid()]))
        mcts_ai = get_ai_algorithm("MCTS_Basic", game, ".")

        eval_mcts_w = evaluate_against_ai(game, player, mcts_ai, True, num_games // 2, config, connection)
        eval_mcts_b = evaluate_against_ai(game, mcts_ai, player, False, num_games // 2, config, connection)

        connection.send((f"perform_mcts", (eval_mcts_w, eval_mcts_b)))
        """

        connection.send(("log", ["Evaluating against macro network", getpid()]))
        macro_ai = get_ai_algorithm("MCTS", game)
        macro_ai.set_config(config)
        # Final evaluation against a previous generation of the neural network
        # (called the 'macro network', i.e: the latest 100th network).
        macro_step = round(step, -2)
        macro_step = macro_step if macro_step < step - 10 else macro_step - config.SAVE_CHECKPOINT_MACRO
        num_games = min(macro_step // 100, 5)

        eval_macro_b = evaluate_against_ai(game, macro_ai, player, False, num_games, config, connection, macro_step)
        eval_macro_w = evaluate_against_ai(game, player, macro_ai, True, num_games, config, connection, macro_step)

        connection.send((f"perform_macro", (eval_macro_w, eval_macro_b)))

    player.cfg.NUM_SAMPLING_MOVES = num_sample_moves # Restore softmax sampling.
    player.cfg.NOISE_BASE = noise_base # Restore noise.

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
        if getpid() == "Process 03":
            evaluate_model(games[0], p1s[0], 1112, config, connection)
        play_games(games, p1s, p2s, config, gui=gui, connection=connection)
        clones = []

        for i in range(len(games)):
            game = games[i]
            p1 = p1s[i]
            p2 = p2s[i]
            clones.append(game.clone())
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
        g = game.clone()
        player_1 = get_ai_algorithm(type(p1).__name__, g, ".")
        player_2 = get_ai_algorithm(type(p2).__name__, g, ".")
        p_1_agents.append(player_1)
        p_2_agents.append(player_2)
        games.append(g)
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
    if connection:
        connection.recv()
    games, player_1_agents, player_2_agents = copy_games_and_players(game, p1, p2, cfg.ACTORS // 3)
    for i in range(1, len(games)):
        player_1_agents[i].set_config(cfg)
        player_2_agents[i].set_config(cfg)

    play_loop(games, player_1_agents, player_2_agents, 0, gui, cfg, connection)
