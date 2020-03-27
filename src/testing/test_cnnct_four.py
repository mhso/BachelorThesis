from testing import assertion
from controller.connect_four import Connect_Four
from model.state import Action
from time import time
from util.excelUtil import ExcelUtil
from util.sqlUtil import SqlUtil
from numpy.random import uniform
import numpy as np

def run_tests():
    # Test possible initial actions.
    test_size = 6
    game = Connect_Four(test_size)
    state = game.start_state()

    expected_actions = [
        Action(None, (test_size-1, 0)), Action(None, (test_size-1, 1)),
        Action(None, (test_size-1, 2)), Action(None, (test_size-1, 3)),
        Action(None, (test_size-1, 4)), Action(None, (test_size-1, 5))
    ]

    assertion.assert_all_equal(expected_actions, game.actions(state), "correct actions")
    # =================================
    # Test possible mid-game actions.
    result = game.result(state, Action(None, (test_size-1, 0)))
    result = game.result(result, Action(None, (test_size-1, 2)))
    result = game.result(result, Action(None, (test_size-2, 0)))

    expected_actions = [
        Action(None, (test_size-3, 0)), Action(None, (test_size-1, 1)),
        Action(None, (test_size-2, 2)), Action(None, (test_size-1, 3)),
        Action(None, (test_size-1, 4)), Action(None, (test_size-1, 5))
    ]

    assertion.assert_all_equal(expected_actions, game.actions(result), "correct actions moved")

    # =================================
    # Test terminal state vertical.

    result.player = not result.player
    result = game.result(result, Action(None, (test_size-3, 0)))
    result.player = not result.player
    result = game.result(result, Action(None, (test_size-4, 0)))

    assertion.assert_true(game.terminal_test(result), "terminal test vertical")

    # =================================
    # Test utility function.
    utility_w = game.utility(result, True)
    utility_b = game.utility(result, False)

    assertion.assert_equal(1, utility_w, "utility white")
    assertion.assert_equal(-1, utility_b, "utility black")

    # =================================
    # Test policy normalization.
    logits = np.array([
        -0.42, 0.23, -0.33, 0.23, -0.11, 0.19,
        -0.42, 0.23, -0.33, 0.23, -0.11, 0.19,
        -0.42, 0.23, -0.33, 0.23, -0.11, 0.19,
        -0.42, 0.23, -0.33, 0.23, -0.11, 0.19,
        -0.42, 0.23, -0.33, 0.23, -0.11, 0.19,
        -0.42, 0.23, -0.33, 0.23, -0.11, 0.19,
    ])
    state = game.start_state()
    mapping = game.map_actions(game.actions(state), logits)


def run_iteration_timing_test(log_type=None):
    # TEST STUFF
    print("run iteration timing test ConnectFour")
    game = Connect_Four(7)
    state = game.start_state()

    time_b = time()

    counter = 0
    while not game.terminal_test(state):
        actions = game.actions(state)
        action = actions[int(uniform(0, len(actions)))]
        state = game.result(state, action)
        counter += 1

    time_taken = time() - time_b
    print("Time taken to play out game: {} s".format(time_taken))
    print("Iterations: {}".format(counter))

    if log_type == 'excel':
        # Appending results to standard excel file "test_results.xlsx"
        row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "ConnectFour", counter, (time() - time_b))
        ExcelUtil.excel_append_row(row)
    elif log_type == 'sql':
        row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "ConnectFour", counter, (time() - time_b))
        sql_conn = SqlUtil.connect()
        SqlUtil.test_iteration_timing_insert_row(sql_conn, row)


    return time_taken
