"""
----------------------------------------------
training: Listen to updates from self-play actors,
train network, predict from network, and plot performance.
----------------------------------------------
"""
import pickle
import os
from multiprocessing.connection import wait
from glob import glob
from sys import argv
from time import time
import datetime
from numpy import array, concatenate
from model.neural import NeuralNetwork
from view.log import FancyLogger
from view.graph import GraphHandler
from config import Config
from util.sqlUtil import SqlUtil

def train_network(network_storage, replay_storage, training_step, game):
    """
    Trains the network by sampling a batch of data
    from the replay buffer. Also plots loss and saves
    these to file if enabed.

    Parameters:
        network_storage - NetworkStorage instance with methods for retrieving
                          the latest generation of the network.
        replay_storage  - ReplayStorage instance with methods for sampling batches
                          of training data, generated during self-play.
        training_step   - The current step/epoch of training.
        game            - The game currently being played.
    
    Returns:
        A boolean value indicating whether training is finished.
    """
    game_name = type(game).__name__
    network = network_storage.latest_network()
    FancyLogger.set_network_status("Training...") # Get the latest network.

    loss = 0
    for i in range(Config.ITERATIONS_PER_TRAINING):
        # Sample batch, to get random game state to train on.
        inputs, expected_out = replay_storage.sample_batch(training_step)

        loss_hist = network.train(inputs, expected_out) # Train and get loss metrics.
        loss = [loss_hist["loss"][-1],
                loss_hist["policy_head_loss"][-1],
                loss_hist["value_head_loss"][-1]]
        if "-s" in argv or "-ds" in argv:
            save_loss(loss, training_step+i, game_name)
        update_loss(loss)
        GraphHandler.plot_data("Average Loss", "Training Loss", training_step+1+i, loss[0])
        GraphHandler.plot_data("Policy Loss", "Training Loss", training_step+1+i, loss[1])
        GraphHandler.plot_data("Value Loss", "Training Loss", training_step+1+i, loss[2])

    if not training_step % Config.SAVE_CHECKPOINT:
        # Create a new neural network with the newly trained model.
        network = NeuralNetwork(game, network.model)
        network_storage.save_network(training_step, network)
        if "-s" in argv:
            network_storage.save_network_to_file(training_step, network, game_name)
        if "-ds" in argv:
            network_storage.save_network_to_sql(network)

    if training_step >= Config.TRAINING_STEPS:
        return True
    return False

def show_performance_data(ai, index, step, data):
    """
    Show data from an evaluation against a specific AI.

    Parameters:
        ai    - The AI that was evaluated against.
        index - Index of the performance type. Used when
                plotting/printing the results.
        step  - The training step where the evaluation ended.
        data  - The evaluation data. Is a list of length 3, with
                data for how well our program performs in total,
                as player 1, and as player 2.
    """
    total = data[0]
    as_white = data[1] if data[1] is not None else 0.0
    as_black = data[2] if data[2] is not None else 0.0
    values = [None, None, None, None]
    values[index] = [total, as_white, as_black]
    update_perf_values(values)

    GraphHandler.plot_data("Training Evaluation", ai, step, total)

def handle_performance_data(step, perform_data, game_name):
    """
    Get performance data from games against alternate AIs.
    Print/plot the results.
    """
    p1 = perform_data[0]
    p2 = perform_data[1]
    p3 = perform_data[2]
    p4 = perform_data[3]
    if p1 is not None:
        show_performance_data("Versus Random", 0, step, p1)
        if "-s" in argv:
            save_perform_data(p1, "random", step, game_name) # Save to file.
        perform_data[0] = None
    elif p2 is not None:
        show_performance_data("Versus Minimax", 1, step, p2)
        if "-s" in argv:
            save_perform_data(p2, "minimax", step, game_name) # Save to file.
        perform_data[1] = None
    elif p3 is not None:
        show_performance_data("Versus MCTS", 2, step, p3)
        if "-s" in argv:
            save_perform_data(p3, "mcts", step, game_name) # Save to file.
        perform_data[2] = None
    elif p4 is not None:
        show_performance_data("Versus Macro Network", 3, step, p4)
        if "-s" in argv:
            save_perform_data(p4, "macro", step, game_name) # Save to file.
        perform_data[3] = None

def game_over(new_games):
    """
    Check whether we should train the network, after a game is finished.

    Returns:
        A boolean value indicating whether the network should train.
    """
    if new_games >= Config.GAMES_PER_TRAINING:
        return True
    return False

def evaluate_games(eval_queue, network_storage):
    """
    Evaluate a queue of games using the specified
    generations of neural networks.

    Parameters:
        eval_queue      - Data structured as dictionaries, which
                          contain dictionaries, which contain lists.
                          The top dictionary maps from network generations
                          to another dictionary, which maps from pipe objects,
                          of a specific process, to data that needs network evaluation.
        network_storage - NetworkStorage instance storing the different networks.
    """
    results = {}
    # Iterate through each network, and associated data, in the queue.
    for n_id, data in eval_queue.items():
        joined = []
        amount = [0] # Keep track of amount of data from each process.
        # Join data for the current network into one batch.
        for conn, vals in data.items():
            joined.extend(vals)
            amount.append(len(vals)+amount[-1])
        arr = array(joined)
        policies, values = network_storage.get_network(n_id).evaluate(arr)

        # For each process, sum up all results into one list.
        for i, conn in enumerate(data):
            old_data = results.get(conn)
            if old_data is None:
                results[conn] = (policies[amount[i]:amount[i+1]], values[amount[i]:amount[i+1], 0])
            else:
                old_policies, old_values = old_data

                old_policies = concatenate((old_policies, policies[amount[i]:amount[i+1]]))
                old_values = concatenate((old_values, values[amount[i]:amount[i+1], 0]))

                results[conn] = (old_policies, old_values)
    
    # Finally, send the relevant evaluation data to all processes.
    for conn, data in results.items():
        conn.send(data)

def load_all_perform_data(game_name):
    perf_rand = load_perform_data("random", None, game_name)
    if perf_rand:
        for t_step, data in perf_rand:
            show_performance_data("Versus Random", 0, t_step, data)
    perf_mini = load_perform_data("minimax", None, game_name)
    if perf_mini:
        for t_step, data in perf_mini:
            show_performance_data("Versus Minimax", 1, t_step, data)
    perf_mcts = load_perform_data("mcts", None, game_name)
    if perf_mcts:
        for t_step, data in perf_mcts:
            show_performance_data("Versus MCTS", 2, t_step, data)
    perf_macro = load_perform_data("macro", None, game_name)
    if perf_macro:
        for t_step, data in perf_macro:
            show_performance_data("Versus Macro Network", 3, t_step, data)

def eval_checkpoint(training_step):
    """
    This method defines how often to evaluate performance against 
    alternate AIs.
    How often this is done changes as the training steps increases.
    """
    checkpoints = Config.EVAL_CHECKPOINT
    if type(checkpoints) is int:
        return checkpoints
    eval_cp = 1
    for k in checkpoints:
        if training_step >= k:
            eval_cp = checkpoints[k]
        else:
            break
    return eval_cp

def parse_load_step(args):
    step = None
    try:
        index = args.index("-l")
        if index < len(args)-1:
            step = int(args[index+1])
    except ValueError:
        pass
    return step

def load_macro_networks(game, network_storage, game_name, step):
    """
    Load all 'macro networks', which are networks from previous
    generations, at every 100th training step. The amount loaded
    depend on the MAX_MACRO_STORAGE parameter.
    """
    steps = []
    while step >= 100 and len(steps) < Config.MAX_MACRO_STORAGE:
        macro_model, macro_step = network_storage.load_macro_network_from_file(step, game_name)
        macro_network = NeuralNetwork(game, model=macro_model)
        network_storage.networks[macro_step] = macro_network
        steps.append(macro_step)
        step = macro_step - 100
    steps.reverse() # Order networks, oldest -> newest.
    network_storage.macro_steps = steps
    print("Loaded all macro networks.")

def initialize_network(game, network_storage, test_mode):
    """
    Initialize the neural network after starting the program.
    If loading is enabled, this network is loaded from file.
    Loss history and evaluation history is also loaded.
    """
    training_step = 0
    # Construct the initial network.
    #if the -l option is selected, load a network from files
    GAME_NAME = type(game).__name__
    if "-l" in argv or "-ln" in argv:
        step = parse_load_step(argv)
        model = network_storage.load_network_from_file(step, GAME_NAME)
        # Load macro network(s).
        if not test_mode: # Don't load macro networks, if we are not actively training.
            load_macro_networks(game, network_storage, GAME_NAME, network_storage.curr_step)

    elif "-dl" in argv:
        model = network_storage.load_newest_network_from_sql()

    if "-l" in argv or "-dl" in argv or "-ln" in argv:
        training_step = network_storage.curr_step + Config.ITERATIONS_PER_TRAINING
        # Load previously saved network loss + performance data.
        losses = [[], [], []]
        for i in range(network_storage.curr_step+1):
            loss_both, loss_pol, loss_val = load_loss(i, GAME_NAME)
            losses[0].append(loss_both)
            losses[1].append(loss_pol)
            losses[2].append(loss_val)
        update_loss([losses[0][-1], losses[1][-1], losses[2][-1]])
        load_all_perform_data(GAME_NAME)

        GraphHandler.plot_data("Average Loss", "Training Loss", None, losses[0])
        GraphHandler.plot_data("Policy Loss", "Training Loss", None, losses[1])
        GraphHandler.plot_data("Value Loss", "Training Loss", None, losses[2])
        # Load newest network.
        network = NeuralNetwork(game, model=model)
        network_storage.save_network(training_step, network)
    else:
        # Create new neural network from scratch.
        network = NeuralNetwork(game)
        network_storage.save_network(0, network)
        FancyLogger.set_network_status("Waiting for data...")
    return training_step

def monitor_games(game_conns, game, network_storage, replay_storage, test_mode=False):
    """
    Listen for updates from self-play processes.
    These include:
        - requests for network evaluation.
        - the result of a terminated game.
        - the result of performance evaluation games.
        - logging events.

    Parameters:
        game_conns  - 'Pipe' objects containing connections to
                     self-playing processes.
        game        - The game to be played and trained on.
        network_storage - NetworkStorage instance storing the different networks.
        replay_storage  - ReplayStorage instance with methods for sampling batches
                          of training data, generated during self-play.
        test_mode       - Whether the program is used in test mode, or training mode.
    """
    game_name = type(game).__name__
    # Setup initial variables.
    start_training_status()
    set_total_steps(Config.TRAINING_STEPS)
    training_step = initialize_network(game, network_storage, test_mode)
    start_timing(game_name)
    update_training_step(training_step)
    update_num_games(replay_storage.get_replay_count(game_name))
    FancyLogger.set_game_and_size(type(game).__name__, game.size)

    # Notify processes that network is ready.
    for conn in game_conns:
        conn.send("go")

    eval_queue = {}
    new_eval_data = 0
    perform_data = [None, None, None, None]
    alert_perform = {game_conns[-1]: False}
    new_games = 0
    new_training_steps = training_step % eval_checkpoint(training_step)

    try:
        while True:
            for conn in wait(game_conns):
            # For all connections to self-play processes.
                status, data = conn.recv()
                if status == "evaluate":
                    # Process has data that needs evaluation from the network.
                    # Add it to the evaluation queue.
                    new_eval_data += 1
                    for n_id, eval_data in data:
                        if eval_queue.get(n_id) is not None:
                            if eval_queue[n_id].get(conn) is None:
                                eval_queue[n_id][conn] = [eval_data]
                            else:
                                eval_queue[n_id][conn].append(eval_data)
                        else:
                            eval_queue[n_id] = {conn: [eval_data]}
                    if new_eval_data == Config.GAME_THREADS:
                        # Enough data is received, send data to evaluation.
                        evaluate_games(eval_queue, network_storage)
                        eval_queue = {}
                        new_eval_data = 0
                elif status == "game_over":
                    # Game is over, add it to game storage.
                    for game in data:
                        update_num_games()
                        replay_storage.save_game(game, training_step)
                        if "-s" in argv:
                            replay_storage.save_replay(game, training_step, game_name)
                        if "-ds" in argv:
                            replay_storage.save_game_to_sql(game)
                        new_games += 1

                        should_train = game_over(new_games)
                        finished = False
                        if should_train:
                            # Tell network to train on a batch of data.
                            new_training_steps += Config.ITERATIONS_PER_TRAINING
                            new_step = training_step + Config.ITERATIONS_PER_TRAINING
                            update_training_step(new_step)
                            finished = train_network(network_storage, replay_storage,
                                                    training_step, game)
                            training_step = new_step
                            new_games = 0
                            if (not finished and Config.EVAL_CHECKPOINT and
                                    new_training_steps >= eval_checkpoint(training_step)):
                                # Indicate that the processes should run performance evaluation games.
                                for k in alert_perform:
                                    # Half should play against AI as player 1, half as player 2.
                                    alert_perform[k] = True
                                new_training_steps = 0
                        if finished:
                            FancyLogger.set_network_status("Training finished!")
                            for c in game_conns:
                                c.close()
                            return
                    if alert_perform.get(conn, False):
                        # Tell the process to start running perform eval games.
                        conn.send(training_step)
                        alert_perform[conn] = False
                    else:
                        # Nothing of note happens, indicate that process should carry on as usual.
                        conn.send(None)
                    if "-s" in argv:
                        time_spent = time() - FancyLogger.time_started
                        save_time_spent(time_spent, game_name)
                        save_run_report(time_spent, game_name)
                elif status == "log":
                    FancyLogger.set_thread_status(data[1], data[0])
                elif status[:7] == "perform":
                    # Get performance data from games against alternate AIs.
                    total = (data[0] + data[1])/2
                    as_white = data[0]
                    as_black = data[1]
                    index = None
                    if status == "perform_rand":
                        index = 0
                    elif status == "perform_mini":
                        index = 1
                    elif status == "perform_mcts":
                        index = 2
                    elif status == "perform_macro":
                        # Evaluation data is against macro networks.
                        # Remove oldest macro network.
                        network_storage.remove_oldest_macros()
                        index = 3

                    perform_data[index] = (total, as_white, as_black)
                    handle_performance_data(training_step, perform_data, game_name)
    except KeyboardInterrupt:
        for conn in game_conns:
            conn.close()
        print("Exiting...")
        update_active(0)
        return
    except (EOFError, BrokenPipeError) as e:
        print(e)
        update_active(0)
        return

def save_perform_data(data, ai, step, game_name):
    location = "../resources/" + game_name + "/misc/"
    filename = "perform_eval_{}_{}.bin".format(ai, step)

    if not os.path.exists((location)):
        os.makedirs((location))

    pickle.dump(data, open(location + filename, "wb"))

def save_loss(loss, step, game_name):
    location = "../resources/" + game_name + "/misc/"
    filename = "loss_{}.bin".format(step)

    if not os.path.exists((location)):
        os.makedirs((location))

    pickle.dump(loss, open(location + filename, "wb"))

def save_run_report(time_spent, game_name):
    location = "../resources/" + game_name + "/"
    filename = "run_report.txt"

    date = datetime.datetime.fromtimestamp(time())
    report = [
        f"=== Run report - {date.ctime()} ===\n",
        f"Time spent: {datetime.timedelta(seconds=int(time_spent))}\n",
        f"Game: {game_name}\n",
        f"Board size: {FancyLogger.board_size}\n",
        f"Training steps: {FancyLogger.train_step}\n",
        FancyLogger.network_status+"\n",
        f"Games generated: {FancyLogger.total_games}"
    ]

    try:
        with open(location + filename, "w") as file:
            file.writelines(report)
    except IOError:
        print("Saving run report failed.")

def save_time_spent(time_spent, game_name):
    location = "../resources/" + game_name + "/misc/"
    filename = "time_spent.bin"
    if not os.path.exists((location)):
        os.makedirs((location))

    pickle.dump(time_spent, open(location + filename, "wb"))

def load_time_spent(game_name):
    try:
        time_spent = pickle.load(open(f"../resources/{game_name}/misc/time_spent.bin", "rb"))
        return time_spent
    except IOError:
        return 0

def load_perform_data(ai, step, game_name):
    """
    Load all performance data for a specific game,
    and a specific step, if specified.
    """
    try:
        data = None
        path = "../resources/" + game_name + "/misc/perform_eval_"
        if step:
            data = pickle.load(open("{}{}_{}.bin".format(path, ai, step), "rb"))
        else:
            data = []
            files = glob("{}{}_*".format(path, ai))
            if files == []:
                return None
            for f in files:
                step = f.strip().split("_")[-1][:-4]
                data.append((int(step), pickle.load(open(f, "rb"))))
            data.sort(key=lambda sd: sd[0])
        return data
    except IOError:
        return None

def load_loss(step, game_name):
    """
    Loads network training loss for given training step.
    If no such data exists, returns 1.
    """
    try:
        loss = pickle.load(open(f"../resources/{game_name}/misc/loss_{step}.bin", "rb"))
        return loss[0], loss[1], loss[2]
    except IOError:
        return 1, 1, 1

def start_timing(game_name):
    FancyLogger.start_timing()
    if "-l" in argv:
        time_spent = load_time_spent(game_name)
        FancyLogger.time_started -= time_spent

def update_training_step(step):
    FancyLogger.set_training_step(step)
    FancyLogger.eval_checkpoint = eval_checkpoint(step)
    if Config.STATUS_DB:
        SqlUtil.set_status(SqlUtil.connection, "step=%s", step)

def update_loss(loss):
    FancyLogger.set_network_status(f"Training loss: Total: {loss[0]:.5f}. Policy: {loss[1]:.5f}. Value: {loss[2]:.5f}")
    if Config.STATUS_DB:
        SqlUtil.set_status(SqlUtil.connection, "loss=%s", float(loss[0]))

def update_num_games(games=None):
    if games is not None:
        FancyLogger.total_games = games
        if Config.STATUS_DB:
            SqlUtil.set_status(SqlUtil.connection, "games=%s", games)
    else:
        FancyLogger.increment_total_games()
        if Config.STATUS_DB:
            SqlUtil.set_status(SqlUtil.connection, "games=games+1")

def update_perf_values(values):
    FancyLogger.set_performance_values(values)
    if Config.STATUS_DB:
        insert_str = None
        val = None
        if values[0] is not None:
            insert_str = "eval_rand=%s"
            val = values[0][0]
        elif values[1] is not None:
            insert_str = "eval_mini=%s"
            val = values[1][0]
        elif values[2] is not None:
            insert_str = "eval_mcts=%s"
            val = values[2][0]
        elif values[3] is not None:
            insert_str = "eval_macro=%s"
            val = values[3][0]
        SqlUtil.set_status(SqlUtil.connection, insert_str, float(val))

def update_active(active):
    if Config.STATUS_DB:
        SqlUtil.set_status(SqlUtil.connection, "active=%s", active)
        if not active:
            SqlUtil.connection.close()

def set_total_steps(steps):
    if Config.STATUS_DB:
        SqlUtil.set_status(SqlUtil.connection, "total_steps=%s", steps)

def start_training_status():
    if Config.STATUS_DB:
        if "-l" in argv:
            load_training_status()
        else:
            SqlUtil.connection = SqlUtil.connect()
            SqlUtil.add_status(SqlUtil.connection)

def load_training_status():
    if Config.STATUS_DB:
        SqlUtil.connection = SqlUtil.connect()
        SqlUtil.get_latest_status(SqlUtil.connection)
        update_active(1)
