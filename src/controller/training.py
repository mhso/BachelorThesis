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
from numpy import array
from model.neural import NeuralNetwork
from view.log import FancyLogger
from view.graph import GraphHandler
from config import Config
from util.sqlUtil import SqlUtil

def train_network(network_storage, replay_storage, training_step, game_name):
    """
    Trains the network by sampling a batch of data
    from replay buffer.
    """
    network = network_storage.latest_network()
    FancyLogger.set_network_status("Training...")

    loss = 0
    for i in range(Config.ITERATIONS_PER_TRAINING):
        inputs, expected_out = replay_storage.sample_batch()

        loss_hist = network.train(inputs, expected_out)
        loss = [loss_hist["loss"][-1],
                loss_hist["policy_head_loss"][-1],
                loss_hist["value_head_loss"][-1]]
        if "-s" in argv or "-ds" in argv:
            save_loss(loss, training_step+i, game_name)
        update_loss(loss[0])
        GraphHandler.plot_data("Average Loss", "Training Loss", training_step+1+i, loss[0])
        GraphHandler.plot_data("Policy Loss", "Training Loss", training_step+1+i, loss[1])
        GraphHandler.plot_data("Value Loss", "Training Loss", training_step+1+i, loss[2])

    if not training_step % Config.SAVE_CHECKPOINT:
        network_storage.save_network(training_step, network)
        if "-s" in argv:
            network_storage.save_network_to_file(training_step, network, game_name)
        if "-ds" in argv:
            network_storage.save_network_to_sql(network)

    if training_step >= Config.TRAINING_STEPS:
        return True
    return False

def show_performance_data(ai, index, step, data):
    total = data[0]
    as_white = data[1] if data[1] is not None else 0.0
    as_black = data[2] if data[2] is not None else 0.0
    values = [None, None, None]
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

def game_over(conn, new_games):
    """
    Handle cases for when a game is completed on a process.
    These include:
        - Train the network if a big enough batch size is ready.
        - Start evaluating performance of MCTS against alternate AI's.
        - Check if training is finished.
    @returns True or false, indicating whether training is complete.
    """
    if new_games >= Config.GAMES_PER_TRAINING:
        return True
    return False

def evaluate_games(game, eval_queue, network_storage):
    """
    Evaluate a queue of games using the latest neural network.
    """
    joined = eval_queue[0][1]
    amount = [0, len(eval_queue[0][1])]
    for i in range(1, len(eval_queue)):
        joined.extend(eval_queue[i][1])
        amount.append(len(eval_queue[i][1])+amount[-1])

    arr = array(joined)
    policies, values = network_storage.latest_network().evaluate(arr)
    # Send result to all processes in the queue.
    g_name = type(game).__name__
    logits = policies if g_name != "Latrunculi" else (policies[0], policies[1])

    for i, data in enumerate(eval_queue):
        conn = data[0]
        conn.send((logits[amount[i]:amount[i+1]], values[amount[i]:amount[i+1], 0]))

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

def eval_checkpoint(training_step):
    """
    This method defines how often to evaluate
    performance against alternate AI's.
    """
    checkpoints = Config.EVAL_CHECKPOINT
    if type(checkpoints) is int:
        return checkpoints
    eval_cp = None
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

def initialize_network(game, network_storage):
    training_step = 0
    # Construct the initial network.
    #if the -l option is selected, load a network from files
    GAME_NAME = type(game).__name__
    if "-l" in argv or "-ln" in argv:
        step = parse_load_step(argv)
        model = network_storage.load_network_from_file(step, GAME_NAME)
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
        update_loss(losses[0][-1])
        load_all_perform_data(GAME_NAME)

        GraphHandler.plot_data("Average Loss", "Training Loss", None, losses[0])
        GraphHandler.plot_data("Policy Loss", "Training Loss", None, losses[1])
        GraphHandler.plot_data("Value Loss", "Training Loss", None, losses[2])
        FancyLogger.start_timing()
        network = NeuralNetwork(game, model=model)
        network_storage.save_network(training_step, network)
        FancyLogger.set_network_status("Training loss: {}".format(losses[0][-1]))
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
    start_training_status()
    set_total_steps(Config.TRAINING_STEPS)
    FancyLogger.start_timing()
    training_step = initialize_network(game, network_storage)
    update_training_step(training_step)
    update_num_games(len(replay_storage.buffer))
    FancyLogger.set_game_and_size(type(game).__name__, game.size)

    # Notify processes that network is ready.
    for conn in game_conns:
        conn.send("go")

    eval_queue = []
    perform_data = [None, None, None]
    alert_perform = {game_conns[-1]: False}
    wins_vs_rand = 0
    new_games = 0
    new_training_steps = training_step % eval_checkpoint(training_step)
    game_name = type(game).__name__

    try:
        while True:
            for conn in wait(game_conns):
                status, val = conn.recv()
                if status == "evaluate":
                    eval_queue.append((conn, val))
                    if len(eval_queue) == Config.GAME_THREADS:
                        evaluate_games(game, eval_queue, network_storage)
                        eval_queue = []
                elif status == "game_over":
                    for game in val:
                        update_num_games()
                        replay_storage.save_game(game)
                        if "-s" in argv:
                            replay_storage.save_replay(game, training_step, game_name)
                        if "-ds" in argv:
                            replay_storage.save_game_to_sql(game)
                        new_games += 1

                        should_train = game_over(conn, new_games)
                        finished = False
                        if should_train:
                            # Tell network to train on a batch of data.
                            new_training_steps += Config.ITERATIONS_PER_TRAINING
                            new_step = training_step + Config.ITERATIONS_PER_TRAINING
                            update_training_step(new_step)
                            finished = train_network(network_storage, replay_storage,
                                                    training_step, game_name)
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
                        conn.send(wins_vs_rand >= 24)
                        alert_perform[conn] = False
                    else:
                        # Nothing of note happens, indicate that process should carry on as usual.
                        conn.send(None)
                elif status == "log":
                    FancyLogger.set_thread_status(val[1], val[0])
                elif status[:7] == "perform":
                    # Get performance data from games against alternate AIs.
                    total = val[0] + val[1]
                    as_white = val[0]
                    as_black = val[1]
                    index = None
                    if status == "perform_rand":
                        if wins_vs_rand < 24:
                            wins_vs_rand = wins_vs_rand + Config.EVAL_GAMES if total == 1 else 0
                        index = 0
                    elif status == "perform_mini":
                        index = 1
                    elif status == "perform_mcts":
                        index = 2

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

def load_perform_data(ai, step, game_name):
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

def update_training_step(step):
    FancyLogger.set_training_step(step)
    FancyLogger.eval_checkpoint = eval_checkpoint(step)
    if Config.STATUS_DB:
        SqlUtil.set_status(SqlUtil.connection, "step=%s", step)

def update_loss(loss):
    FancyLogger.set_network_status("Training loss: {}".format(loss))
    if Config.STATUS_DB:
        SqlUtil.set_status(SqlUtil.connection, "loss=%s", float(loss))

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
