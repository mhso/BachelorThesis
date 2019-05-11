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

def create_roots(batch_data):
    """
    Create root nodes for use in MCTS simulation. Takes as a parameter a list of tuples,
    containing data for each game. This data consist of: gametype, state, type of player 1
    and type of player 2
    """
    root_nodes = []
    for data in batch_data:
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]

        player = player_1 if game.player(state) else player_2
        root_nodes.append(player.create_root_node(state))
    return root_nodes

def prepare_actions(batch_data, roots):
    """
    Add exploration noise and check for 'pass' action
    on a batch of nodes.
    """
    for i, data in enumerate(batch_data):
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        root = roots[i]

        player = player_1 if game.player(state) else player_2

        player.prepare_action(root)

def select_nodes(batch_data, roots):
    """
    Run 'select' in MCTS on a batch of root nodes.
    """
    nodes = []
    for i, root in enumerate(roots):
        data = batch_data[i]
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        root = roots[i]

        player = player_1 if game.player(state) else player_2

        nodes.append(player.select(root))
    return nodes

def expand_nodes(batch_data, nodes, policies, values):
    """
    Expand a batch of node based on policy logits
    acquired from the neural network.
    """
    return_values = []
    for i, node in enumerate(nodes):
        data = batch_data[i]
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        policy = policies[i]

        player = player_1 if game.player(state) else player_2
        return_values.append(player.set_evaluation_data(node, policy, values[i]))
    return return_values

def backprop_nodes(batch_data, nodes, values):
    """
    Backpropagate values from the neural network
    to update a batch of nodes.
    """
    for i, node in enumerate(nodes):
        data = batch_data[i]
        game = data[0]
        state = data[1]
        player_1 = data[2]
        player_2 = data[3]
        value = values[i]

        player = player_1 if game.player(state) else player_2

        player.back_propagate(node, node.state.player, -value)

def pack_data_for_eval(batch_data, networks, nodes):
    return [(-1 if networks is None else networks[g[0]][g[1].player],
             g[0].structure_data(n.state)) for (g, n) in zip(batch_data, nodes)]

def play_as_mcts(batch_data, networks, config, connection):
    """
    Play a batch of games as MCTS vs. MCTS.
    """
    roots = create_roots(batch_data)

    # Get network evaluation from main process.
    data = pack_data_for_eval(batch_data, networks, roots)
    connection.send(("evaluate", data))

    policies, values = connection.recv()
    log(f"Root policies:\n{policies}")
    log(f"OG root values: {values}")
    values = expand_nodes(batch_data, roots, policies, values)
    prepare_actions(batch_data, roots)

    for _ in range(config.MCTS_ITERATIONS):
        selected_nodes = select_nodes(batch_data, roots)

        data = pack_data_for_eval(batch_data, networks, selected_nodes)
        connection.send(("evaluate", data))
        policies, values = connection.recv()
        values = expand_nodes(batch_data, selected_nodes, policies, values)
        backprop_nodes(batch_data, selected_nodes, values)
    return roots

def play_games(games, w_players, b_players, config, network_steps=None, gui=None, connection=None):
    """
    Play a number of games to the end, with capabilities for playing as any
    type of agent and any type of game.

    Parameters:
        games         - List of game objects to be played out, the state of the games
                        (result and state history) are updated during the process.
        w_players     - List of agents controlling the white pieces.
        b_players     - List of agents controlling the black pieces.
        config        - Config object with a variety of parameters to be used during the game.
        network_steps - Dictionary of game -> dict, mapping which game should target which
                        generation of neural network. Only relevant if MCTS is used.
        gui           - GUI object used to visualize the games, only available if batch-play
                        is not active, meaning only one game is played.
        connection    - Pipe object with connection to the main process. Used when requesting
                        network evaluating among other things.
    """
    # List of lists. Each containing a game to be played,
    # the current state for that game, the agent playing as player1,
    # and the agent playing as player 2.
    batch_data = [[games[i], games[i].start_state(), w_players[i], b_players[i]] for i in range(len(games))]
    total_games = len(games)
    counters = [0 for _ in games] # Counting amount of moves for each game.

    if gui is not None:
        sleep(1)
        # Update GUI, to clear board, if several games are played sequentially.
        gui.update(batch_data[0][1])

    while batch_data:
        player = batch_data[0][2] if batch_data[0][0].player(batch_data[0][1]) else batch_data[0][3]
        time_turn = time()
        if is_mcts(player):
            # Run MCTS simulations. Get resulting root nodes.
            roots = play_as_mcts(batch_data, network_steps, config, connection)

        finished_games_indexes = []
        for (i, (game, state, player_1, player_2)) in enumerate(batch_data):
            player = player_1 if game.player(state) else player_2
            # execute_action receives a root node if player is MCTS, else it gives a state.
            state = player.execute_action(roots[i] if is_mcts(player) else state)
            batch_data[i][1] = state

            if gui is not None:
                if type(w_players).__name__ != "Human" and not state.player:
                    sleep(config.GUI_AI_SLEEP)
                elif type(b_players).__name__ != "Human" and state.player:
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
                # Append state to game history, unless the state is terminal.
                game.history.append(state)

        turn_took = "{0:.3f}".format((time() - time_turn))
        num_active = len(batch_data)
        num_moves = len(batch_data[0][0].history)
        name_1, name_2 = type(batch_data[0][2]).__name__, type(batch_data[0][3]).__name__
        elems_removed = 0
        # Removes games that are finished.
        for i in finished_games_indexes:
            batch_data.pop(i-elems_removed)
            elems_removed += 1

        num_active -= elems_removed
        if connection:
            # Send logging information to main process if playing as MCTS.
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

def evaluate_against_ai(game, player1, player2, eval_player, num_games, config, connection, step=None):
    """
    Evaluate MCTS/NN model against a given AI algorithm.
    Plays out a given number of games and returns
    the ratio of games won by 'eval_player' in the range -1 to 1.

    Parameters:
        game        - Game subclass instance, indicating the game to be played.
        player1     - The agent playing as player 1.
        player2     - The agent playing as player 2.
        eval_player - The player to evaluate wins for.
        num_games   - How many games to evaluate on.
        config      - Config object with a variety of parameters to be used during the game.
        connection  - Pipe object with connection to the main process. Used when requesting
                      network evaluating and for returning the result of the evaluation.
        step        - If not None, indicates the newest 'macro network' to evaluate against.

    Returns:
        Ratio of games won by 'eval_player'.
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
            network_steps[games[i]] = {eval_player: -1, not eval_player: step - (i * 100)}

    network_steps = network_steps if network_steps != {} else None

    play_games(games, p1s, p2s, config, network_steps=network_steps, connection=connection)
    for g in games:
        val = g.terminal_value
        win_v = val if eval_player or val == 0 else -val
        wins += win_v
    game.reset()
    return wins/num_games # Return ratio of games won.

def minimax_for_game(game):
    """
    Returns the relevant Minimax agent for the given game.
    """
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
    Evaluate MCTS/NN model against different AI
    algorithms.

    Parameters:
        game       - Game subclass instance, indicating the game to be played.
        player     - The MCTS agent to be evaluated.
        step       - The current training step (sent from the main process).
        config     - Config object with a variety of parameters to be used during the game.
        connection - Pipe object with connection to the main process. Used when requesting
                     network evaluating and for returning the result of the evaluation.
    """
    num_games = config.EVAL_GAMES
    num_sample_moves = player.cfg.NUM_SAMPLING_MOVES
    noise_base = player.cfg.NOISE_BASE
    player.cfg.NUM_SAMPLING_MOVES = 0 # Disable softmax sampling during evaluation.
    player.cfg.NOISE_BASE = 0 # Disable noise during evaluation.
    connection.send(("log", ["Evaluating against Random", getpid()]))
    rand_ai = get_ai_algorithm("Random", game, ".")

    # Evaluate against AI making random moves.
    eval_rand_w = evaluate_against_ai(game, player, rand_ai, True, num_games // 2, config, connection)
    eval_rand_b = evaluate_against_ai(game, rand_ai, player, False, num_games // 2, config, connection)

    connection.send((f"perform_rand", (eval_rand_w, eval_rand_b)))
    if step > 100:
        # If we are far enough into training,
        # we additionally evaluate against MCTS and Macro Networks.
        # We do not use Minimax, as it is too slow.
        """
        connection.send(("log", ["Evaluating against Minimax", getpid()]))
        mini_ai = get_ai_algorithm("Minimax", game, ".")

        eval_mini_w = evaluate_against_ai(game, player, mini_ai, True, num_games // 2, config, connection)
        eval_mini_b = evaluate_against_ai(game, mini_ai, player, False, num_games // 2, config, connection)

        connection.send((f"perform_mini", (eval_mini_w, eval_mini_b)))
        """
        connection.send(("log", ["Evaluating against basic MCTS", getpid()]))
        mcts_ai = get_ai_algorithm("MCTS_Basic", game, ".")

        # Evaluate against basic MCTS with rollouts.
        eval_mcts_w = evaluate_against_ai(game, player, mcts_ai, True, num_games // 2, config, connection)
        eval_mcts_b = evaluate_against_ai(game, mcts_ai, player, False, num_games // 2, config, connection)

        connection.send((f"perform_mcts", (eval_mcts_w, eval_mcts_b)))

        connection.send(("log", ["Evaluating against macro network", getpid()]))
        macro_ai = get_ai_algorithm("MCTS", game)
        macro_ai.set_config(config)

        # Final evaluation against previous generations of the neural network
        # (called the 'macro networks', i.e: 5 of the latest 100th networks).
        macro_step = round(step, -2)
        macro_step = macro_step if macro_step < step - 10 else macro_step - config.SAVE_CHECKPOINT_MACRO
        num_games = min(macro_step // 100, 5)

        eval_macro_w = evaluate_against_ai(game, player, macro_ai, True, num_games, config, connection, macro_step)
        eval_macro_b = evaluate_against_ai(game, macro_ai, player, False, num_games, config, connection, macro_step)

        connection.send((f"perform_macro", (eval_macro_w, eval_macro_b)))

    player.cfg.NUM_SAMPLING_MOVES = num_sample_moves # Restore softmax sampling.
    player.cfg.NOISE_BASE = noise_base # Restore noise.

def get_game(game_name, size, rand_seed=None, wildcard="."):
    """
    Method for dynamically importing and initializing
    the game given by 'game_name' (if it exists).

    Parameters:
        game_name - Name of the game to import, initialize, and return.
        size      - Board size of the game.
        rand_seed - Only used when the given game is 'Latrunculi'. If the argument is
                    an integer, it is used as a seed for providing a randomly
                    instantiated game board. If 'rand_seed' is the specific string
                    'random', the seed is determined by numpy's random generator.
    Returns:
        An instance of the desired game.
    Raises:
        ImportError - 'game_name' does not correspond the name of an existing game.
    """
    lower = game_name.lower()
    if lower == wildcard:
        game_name = Config.DEFAULT_GAME
        lower = game_name.lower()
    try:
        module = __import__("controller.{}".format(lower), fromlist=["{}".format(game_name)])
        game_class = getattr(module, "{}".format(game_name))
        return game_class(size, rand_seed)
    except ImportError:
        print("Unknown game, name must equal name of game class.")
        return None, "unknown"

def get_ai_algorithm(algorithm, game, wildcard="."):
    """
    Method for dynamically importing and initializing
    the AI agent given by 'algorithm' (if it exists).

    Parameters:
        algorithm - Name of the AI to import, initialize, and return.
        game      - The game that the AI should operate on.
    Returns:
        An instance of the desired agent.
    Raises:
        ImportError - 'algorithm' does not correspond the name of an existing AI.
    """
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
    Run a given number of games with a given AI.

    Parameters:
        games      - A list of games to play.
        p1s        - A list of agents playing as player 1.
        p2s        - A list of agents playing as player 2.
        iteration  - This method is called recursively, and iteration
                    indicates how many games have been played.
        gui        - GUI object used to visualize the games.
        config     - Config object with a variety of parameters to be used during the games.
        connection - Pipe object with connection to the main process. Used when requesting
                     network evaluating among many things.
    """
    if iteration == config.GAME_ITERATIONS:
        print("{} is done with training!".format(getpid()))
        return
    try:
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
    """
    Method for copying the given game, player 1 agent,
    and player 2 agent 'amount' times.

    Returns:
        A tuple of list with games and agents.
    """
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
    """
    Initializes the given game and agents, and starts the self-play loop.
    Called when starting a new self-play process from the main monitor process.

    Parameters:
        game       - Game subclass instance, indicating the game to be played.
        p1         - The agent(s) playing as player 1.
        p2         - The agent(s) playing as player 2.
        connection - Pipe object with connection to the main process. Used when requesting
                     network evaluating among many things.
        gui        - GUI object used to visualize the games.
        config     - Config object with a variety of parameters to be used during the games.
    """
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
