from testing import assertion
from controller.othello import Othello
from model.state import Action

def run_tests():
    # Test terminal state cases.

    # Test white wins.
    game = Othello(6)
    state = game.start_state()
    state.board[:4][:] = 1
    state.board[4:][:] = -1

    game_over = game.terminal_test(state)
    utility_w = game.utility(state, True)
    utility_b = game.utility(state, False)

    assertion.assert_true(game_over, "Terminal test - white wins")
    assertion.assert_equal(1, utility_w, "Utility - white wins")
    assertion.assert_equal(-1, utility_b, "Utility - black loses")

    # =================================
    # Test black wins.
    state = game.start_state()
    state.board[:2][:] = 1
    state.board[2:][:] = -1

    game_over = game.terminal_test(state)
    utility_w = game.utility(state, True)
    utility_b = game.utility(state, False)

    assertion.assert_true(game_over, "Terminal test - black wins")
    assertion.assert_equal(1, utility_b, "Utility - black wins")
    assertion.assert_equal(-1, utility_w, "Utility - white loses")

    # =================================
    # Test white wins by eliminating all black pieces.
    state = game.start_state()
    state.board[2, 2:4] = 1
    state.board[3, 2:4] = 1

    game_over = game.terminal_test(state)
    utility_w = game.utility(state, True)
    utility_b = game.utility(state, False)

    assertion.assert_true(game_over, "Terminal test2 - black wins")
    assertion.assert_equal(1, utility_w, "Utility2 - white wins")
    assertion.assert_equal(-1, utility_b, "Utility2 - black loses")

    # =================================
    # Test tie.
    state = game.start_state()
    state.board[:3][:] = 1
    state.board[3:][:] = -1

    game_over = game.terminal_test(state)
    utility_w = game.utility(state, True)
    utility_b = game.utility(state, False)

    assertion.assert_true(game_over, "Terminal test - tie")
    assertion.assert_equal(0, utility_w, "Utility - black draws")
    assertion.assert_equal(0, utility_b, "Utility - white draws")

    # =================================
    # Test pass move.
    state = game.start_state()
    state.board[3, 2:4] = 0

    actions_w = game.actions(state)
    result = game.result(state, actions_w[0])
    actions_b = game.actions(result)
    result = game.result(result, actions_b[0])
    game_over = game.terminal_test(state)

    assertion.assert_equal([Action((2, 1), None)], actions_w, "Actions - one move")
    assertion.assert_equal([None], actions_b, "Actions - no moves black")
    assertion.assert_equal([None], game.actions(result), "Actions - no moves white")
    assertion.assert_true(result.player, "Actions - pass switches turn")
