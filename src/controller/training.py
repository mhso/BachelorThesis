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

def train_network(network_storage, replay_storage, training_step, game_name):
    """
    Trains the network by sampling a batch of data
    from replay buffer.
    """
    network = network_storage.latest_network()
    FancyLogger.set_network_status("Training...")

    FancyLogger.set_training_step((training_step+1))
    inputs, expected_out = replay_storage.sample_batch()

    loss = network.train(inputs, expected_out)
    if not training_step % Config.SAVE_CHECKPOINT:
        network_storage.save_network(training_step, network)
        if "-s" in argv:
            network_storage.save_network_to_file(training_step, network, game_name)
        if "-ds" in argv:
            network_storage.save_network_to_sql(network)
        if "-s" in argv or "-ds" in argv:
            save_loss(loss, training_step, game_name)

    FancyLogger.set_network_status("Training loss: {}".format(loss[0]))
    GraphHandler.plot_data("Training Loss Combined", "Training Loss", training_step+1, loss[0])
    GraphHandler.plot_data("Training Loss Policy", "Training Loss", training_step+1, loss[1])
    GraphHandler.plot_data("Training Loss Value", "Training Loss", training_step+1, loss[2])

    if training_step == Config.TRAINING_STEPS:
        return True
    return False

def show_performance_data(ai, index, step, data):
    avg_data = sum(data) / len(data)
    values = [None, None, None]
    values[index] = avg_data
    FancyLogger.set_performance_values(values)
    GraphHandler.plot_data("Training Evaluation", ai, step, avg_data)

def handle_performance_data(step, perform_data, perform_size, game_name):
    """
    Get performance data from games against alternate AIs.
    Print/plot the results.
    """
    p1 = perform_data[0]
    p2 = perform_data[1]
    p3 = perform_data[2]
    if len(p1) >= perform_size:
        show_performance_data("Versus Random", 0, step, p1)
        if "-s" in argv:
            save_perform_data(perform_data[0], "random", step, game_name) # Save to file.
        perform_data[0] = []
    elif len(p2) >= perform_size:
        show_performance_data("Versus Minimax", 1, step, p2)
        if "-s" in argv:
            save_perform_data(perform_data[1], "minimax", step, game_name) # Save to file.
        perform_data[1] = []
    elif len(p3) >= perform_size:
        show_performance_data("Versus MCTS", 2, step, p3)
        if "-s" in argv:
            save_perform_data(perform_data[2], "mcts", step, game_name) # Save to file.
        perform_data[2] = []

def game_over(conn, new_games, alert_perform, perform_status):
    """
    Handle cases for when a game is completed on a process.
    These include:
        - Train the network if a big enough batch size is ready.
        - Start evaluating performance of MCTS against alternate AI's.
        - Check if training is finished.
    @returns True or false, indicating whether training is complete.
    """
    if alert_perform.get(conn, False):
        # Tell the process to start running perform eval games.
        alert_perform[conn] = False
        conn.send(perform_status)
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

def parse_load_step(args):
    index = args.index("-l")
    step = None
    if index < len(args)-1:
        try:
            step = int(args[index+1])
        except ValueError:
            pass
    return step

def initialize_network(game, network_storage):
    training_step = 0
    # Construct the initial network.
    #if the -l option is selected, load a network from files
    GAME_NAME = type(game).__name__
    if "-l" in argv:
        step = parse_load_step(argv)
        model = network_storage.load_network_from_file(step, GAME_NAME)
    elif "-dl" in argv:
        model = network_storage.load_newest_network_from_sql()

    if "-l" in argv or "-dl" in argv:
        training_step = network_storage.curr_step+1
        FancyLogger.set_training_step(training_step)
        # Load previously saved network loss + performance data.
        losses = [[], [], []]
        for i in range(training_step):
            loss_both, loss_pol, loss_val = load_loss(i, GAME_NAME)
            losses[0].append(loss_both)
            losses[1].append(loss_pol)
            losses[2].append(loss_val)
        load_all_perform_data(GAME_NAME)

        GraphHandler.plot_data("Training Loss Combined", "Training Loss", None, losses[0])
        GraphHandler.plot_data("Training Loss Policy", "Training Loss", None, losses[1])
        GraphHandler.plot_data("Training Loss Value", "Training Loss", None, losses[2])
        FancyLogger.start_timing()
        network = NeuralNetwork(game, model=model)
        network_storage.save_network(training_step-1, network)
        FancyLogger.set_network_status("Training loss: {}".format(losses[-1]))
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
    FancyLogger.start_timing()
    training_step = initialize_network(game, network_storage)
    FancyLogger.total_games = len(replay_storage.buffer)
    FancyLogger.set_game_and_size(type(game).__name__, game.size)

    # Notify processes that network is ready.
    for conn in game_conns:
        conn.send("go")

    eval_queue = []
    queue_size = Config.GAME_THREADS
    perform_data = [[], [], []]
    perform_size = Config.EVAL_PROCESSES if Config.GAME_THREADS > 1 else 1
    alert_perform = {conn: False for conn in game_conns[-perform_size:]}
    wins_vs_rand = 0
    new_games = 0
    game_name = type(game).__name__

    while True:
        try:
            for conn in wait(game_conns):
                status, val = conn.recv()
                if status == "evaluate":
                    # Process has data that needs to be evaluated. Add it to the queue.
                    eval_queue.append((conn, val))
                    if len(eval_queue) == queue_size:
                        evaluate_games(game, eval_queue, network_storage)
                        eval_queue = []
                elif status == "game_over":
                    FancyLogger.increment_total_games()
                    replay_storage.save_game(val)
                    if "-s" in argv:
                        replay_storage.save_replay(val, training_step, game_name)
                    if "-ds" in argv:
                        replay_storage.save_game_to_sql(val)
                    new_games += 1
                    
                    should_train = game_over(conn, new_games, alert_perform, wins_vs_rand)
                    finished = False
                    if should_train:
                        # Tell network to train on a batch of data.
                        finished = train_network(network_storage, replay_storage,
                                                 training_step, game_name)
                        training_step += 1
                        new_games = 0
                        if not finished and not training_step % Config.EVAL_CHECKPOINT:
                            # Indicate that the processes should run performance evaluation games.
                            for k in alert_perform:
                                alert_perform[k] = True
                    if finished:
                        FancyLogger.set_network_status("Training finished!")
                        for c in game_conns:
                            c.close()
                        return
                elif status == "log":
                    FancyLogger.set_thread_status(val[1], val[0])
                elif status[:7] == "perform":
                    # Get performance data from games against alternate AIs.
                    if status == "perform_rand":
                        games_played = (Config.EVAL_GAMES // Config.EVAL_PROCESSES)
                        wins_vs_rand = wins_vs_rand + games_played if val == 1 else 0
                        perform_data[0].append(val)
                    elif status == "perform_mini":
                        perform_data[1].append(val)
                    elif status == "perform_mcts":
                        perform_data[2].append(val)

                    handle_performance_data(training_step, perform_data, perform_size, game_name)
        except KeyboardInterrupt:
            for conn in game_conns:
                conn.close()
            print("Exiting...")
            return
        except EOFError as e:
            print(e)
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
                step = f.split("_")[-1][:-4]
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
        loss = pickle.load(open(f"../resources/" + game_name + "/misc/loss_{step}.bin", "rb"))
        return loss[0], loss[1], loss[2]
    except IOError:
        return 1
