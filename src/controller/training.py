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
    for _ in range(10):
        inputs, expected_out = replay_storage.sample_batch()

        loss_hist = network.train(inputs, expected_out)
        loss = [loss_hist["loss"][-1],
                loss_hist["policy_head_loss"][-1],
                loss_hist["value_head_loss"][-1]]
    if not training_step % Config.SAVE_CHECKPOINT:
        network_storage.save_network(training_step, network)
        if "-s" in argv:
            network_storage.save_network_to_file(training_step, network, game_name)
        if "-ds" in argv:
            network_storage.save_network_to_sql(network)
        if "-s" in argv or "-ds" in argv:
            save_loss(loss, training_step, game_name)

    update_loss(loss[0])
    GraphHandler.plot_data("Average Loss", "Training Loss", training_step+1, loss[0])
    GraphHandler.plot_data("Policy Loss", "Training Loss", training_step+1, loss[1])
    GraphHandler.plot_data("Value Loss", "Training Loss", training_step+1, loss[2])

    if training_step == Config.TRAINING_STEPS:
        return True
    return False

def show_performance_data(ai, index, step, data):
    avg_total = sum(data[0]) / len(data[0])
    avg_white = sum(data[1]) / len(data[1]) if len(data[1]) else 0.0
    avg_black = sum(data[2]) / len(data[2]) if len(data[2]) else 0.0
    values = [None, None, None]
    values[index] = [avg_total, avg_white, avg_black]
    update_perf_values(values)

    GraphHandler.plot_data("Training Evaluation", ai, step, avg_total)

def handle_performance_data(step, perform_data, perform_size, game_name):
    """
    Get performance data from games against alternate AIs.
    Print/plot the results.
    """
    p1 = perform_data[0]
    p2 = perform_data[1]
    p3 = perform_data[2]
    if len(p1[0]) >= perform_size:
        show_performance_data("Versus Random", 0, step, p1)
        if "-s" in argv:
            save_perform_data(p1, "random", step, game_name) # Save to file.
        perform_data[0] = [[], [], []]
    elif len(p2[0]) >= perform_size:
        show_performance_data("Versus Minimax", 1, step, p2)
        if "-s" in argv:
            save_perform_data(p2, "minimax", step, game_name) # Save to file.
        perform_data[1] = [[], [], []]
    elif len(p3[0]) >= perform_size:
        show_performance_data("Versus MCTS", 2, step, p3)
        if "-s" in argv:
            save_perform_data(p3, "mcts", step, game_name) # Save to file.
        perform_data[2] = [[], [], []]

def game_over(conn, new_games, alert_perform, perform_status):
    """
    Handle cases for when a game is completed on a process.
    These include:
        - Train the network if a big enough batch size is ready.
        - Start evaluating performance of MCTS against alternate AI's.
        - Check if training is finished.
    @returns True or false, indicating whether training is complete.
    """
    alert_status = alert_perform.get(conn, False)
    if alert_status:
        # Tell the process to start running perform eval games.
        conn.send((perform_status, alert_status))
        alert_perform[conn] = 0
    else:
        # Nothing of note happens, indicate that process should carry on as usual.
        conn.send(None)
    if new_games >= Config.GAMES_PER_TRAINING:
        return True
    return False

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
        training_step = network_storage.curr_step+1
        update_training_step(training_step)
        # Load previously saved network loss + performance data.
        losses = [[], [], []]
        for i in range(training_step):
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
        network_storage.save_network(training_step-1, network)
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
    update_num_games(len(replay_storage.buffer))
    FancyLogger.set_game_and_size(type(game).__name__, game.size)

    # Notify processes that network is ready.
    for conn in game_conns:
        conn.send("go")

    eval_queue = []
    queue_size = Config.GAME_THREADS
    perform_data = [[[], [], []], [[], [], []], [[], [], []]]
    perform_size = Config.EVAL_PROCESSES if Config.GAME_THREADS > 1 else 1
    alert_perform = {conn: 0 for conn in game_conns[-perform_size:]}
    wins_vs_rand = 0
    new_games = 0
    game_name = type(game).__name__

    try:
        while True:
            for conn in wait(game_conns):
                status, val = conn.recv()
                if status == "evaluate":
                    # Process has data that needs to be evaluated. Add it to the queue.
                    eval_queue.append((conn, val))
                    if len(eval_queue) == queue_size:
                        evaluate_games(game, eval_queue, network_storage)
                        eval_queue = []
                elif status == "game_over":
                    update_num_games()
                    replay_storage.save_game(val)
                    if "-s" in argv:
                        replay_storage.save_replay(val, training_step, game_name)
                    if "-ds" in argv:
                        replay_storage.save_game_to_sql(val)
                    new_games += 1

                    should_train = game_over(conn, new_games, alert_perform, wins_vs_rand >= 24)
                    finished = False
                    if should_train:
                        # Tell network to train on a batch of data.
                        update_training_step(training_step+1)
                        finished = train_network(network_storage, replay_storage,
                                                 training_step, game_name)
                        training_step += 1
                        new_games = 0
                        if (not finished and Config.EVAL_CHECKPOINT and
                                training_step % eval_checkpoint(training_step) == 0):
                            # Indicate that the processes should run performance evaluation games.
                            for i, k in enumerate(alert_perform):
                                # Half should play against AI as player 1, half as player 2.
                                alert_perform[k] = 1 if i < perform_size/2 else 2
                    if finished:
                        FancyLogger.set_network_status("Training finished!")
                        for c in game_conns:
                            c.close()
                        return
                elif status == "log":
                    FancyLogger.set_thread_status(val[1], val[0])
                elif status[:7] == "perform":
                    # Get performance data from games against alternate AIs.
                    perform_list = None
                    if status[:-2] == "perform_rand":
                        games_played = (Config.EVAL_GAMES // Config.EVAL_PROCESSES)
                        if wins_vs_rand < 24:
                            wins_vs_rand = wins_vs_rand + games_played if val == 1 else 0
                        perform_list = perform_data[0]
                    elif status[:-2] == "perform_mini":
                        perform_list = perform_data[1]
                    elif status[:-2] == "perform_mcts":
                        perform_list = perform_data[2]

                    perform_list[0].append(val) # Score total.
                    if status[-1] == "1":
                        # Score as white.
                        perform_list[1].append(val)
                    else:
                        # Score as black.
                        perform_list[2].append(val)

                    handle_performance_data(training_step, perform_data, perform_size, game_name)
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
    FancyLogger.eval_checkpoint = eval_checkpoint(training_step)
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
