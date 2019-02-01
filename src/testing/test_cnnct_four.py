from testing import assertion
from controller.connect_four import ConnectFour
from model.state import Action
from time import time
from numpy.random import uniform

def run_tests():
    # Test possible initial actions.
    test_size = 7
    game = ConnectFour(test_size)
    state = game.start_state()

    expected_actions = [
        Action((test_size-2, 0), None), Action((test_size-2, 1), None),
        Action((test_size-2, 2), None), Action((test_size-2, 3), None),
        Action((test_size-2, 4), None), Action((test_size-2, 5), None),
        Action((test_size-2, 6), None)
    ]

    assertion.assert_all_equal(expected_actions, game.actions(state), "correct actions")

    # =================================
    # Test possible mid-game actions.
    result = game.result(state, Action((test_size-2, 0), None))
    result = game.result(result, Action((test_size-2, 2), None))
    result = game.result(result, Action((test_size-3, 0), None))

    expected_actions = [
        Action((test_size-4, 0), None), Action((test_size-2, 1), None),
        Action((test_size-3, 2), None), Action((test_size-2, 3), None),
        Action((test_size-2, 4), None), Action((test_size-2, 5), None),
        Action((test_size-2, 6), None)
    ]

    assertion.assert_all_equal(expected_actions, game.actions(result), "correct actions")

    # =================================
    # Test terminal state vertical.

    result.player = not result.player
    result = game.result(result, Action((test_size-4, 0), None))
    result.player = not result.player
    result = game.result(result, Action((test_size-5, 0), None))

    assertion.assert_true(game.terminal_test(result), "terminal test vertical")

    """
    game = ConnectFour(7)
    state = game.start_state()

    time_b = time()

    counter = 0
    while not game.terminal_test(state):
        actions = game.actions(state)
        action = actions[int(uniform(0, len(actions)))]
        state = game.result(state, action)
        counter += 1

    print("Time taken to play out game: {} s".format(time() - time_b))
    print("Iterations: {}".format(counter))
    """
    