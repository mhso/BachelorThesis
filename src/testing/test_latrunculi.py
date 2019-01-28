from testing import assertion
from controller.latrunculi import Latrunculi
from model.state import Action
from numpy import array

def run_tests():
    print("-=-=-=- LATRUNCULI GAME TESTS -=-=-=-")
    # Test initial board setup.

    # Test correct board size.
    test_size = 8
    game = Latrunculi(test_size)
    state = game.start_state()
    assertion.assert_equal(test_size, state.board.shape[1], "correct board width")
    assertion.assert_equal(test_size, state.board.shape[0], "correct board height")

    # =================================
    # "Chess" distribution.
    # Test number of white and black pieces are equal, and is the correct amount.
    num_white = (state.board == 1).sum()
    num_black = (state.board == -1).sum()

    assertion.assert_equal(16, num_black, "number of black pieces chess formation")
    assertion.assert_equal(16, num_white, "number of white pieces chess formation")

    # =================================
    # Random distribution.
    # Test number of white and black pieces are equal, and is the correct amount.
    game = Latrunculi(8, 432)
    state = game.start_state()
    num_white = (state.board == 1).sum()
    num_black = (state.board == -1).sum()

    assertion.assert_equal(16, num_black, "number of black pieces random")
    assertion.assert_equal(16, num_white, "number of white pieces random")

    # =================================
    # Test initial player turn is white.
    assertion.assert_true(game.player(state), "initial player turn")

    # =================================
    # Test terminal state methods.
    # Test terminal_test.
    game = Latrunculi(8)
    state = game.start_state()
    state.board[-3:][:] = 0 # Set white's pieces, except 1, to empty squares.
    state.board[-1][0] = 1

    assertion.assert_true(game.terminal_test(state), "terminal state true")

    # =================================
    # Test utility function.

    assertion.assert_equal(0, game.utility(state, True), "utility white")
    assertion.assert_equal(1, game.utility(state, False), "utility black")

    # =================================
    # Test available actions.
    game = Latrunculi(5)
    state = game.start_state()
    legal_moves = [
        Action((3, 0), (2, 0)), Action((3, 1), (2, 1)), Action((3, 2), (2, 2)),
        Action((3, 3), (2, 3)), Action((3, 4), (2, 4)),
        Action((4, 0), (2, 0)), Action((4, 1), (2, 1)), Action((4, 2), (2, 2)),
        Action((4, 3), (2, 3)), Action((4, 4), (2, 4))
    ]

    assertion.assert_all_equal(legal_moves, game.actions(state), "legal moves white")

    # =================================
    # Test result of action.
    # Test simple move.

    result = game.result(state, Action((3, 0), (2, 0)))
    old_piece = state.board[3][0]
    old_vacant = state.board[2][0]
    new_vacant = result.board[3][0]
    new_piece = result.board[2][0]

    assertion.assert_true(old_piece == new_piece, "regular move piece moved")
    assertion.assert_true(old_vacant == new_vacant, "regular move piece absent")

    # =================================
    # Test jump.
    result = game.result(state, Action((4, 1), (2, 1)))
    old_piece = state.board[4][1]
    old_vacant = state.board[2][1]
    new_vacant = result.board[4][1]
    new_piece = result.board[2][1]

    assertion.assert_true(old_piece == new_piece, "jump move piece moved")
    assertion.assert_true(old_vacant == new_vacant, "jump move piece absent")

    # =================================
    # Test move causing piece to be captured.
    game = Latrunculi(5, 42)
    state = game.start_state()

    result_cb = game.result(state, Action((4, 3), (3, 3)))
    state.player = not state.player
    result_cw = game.result(state, Action((1, 0), (2, 0)))

    assertion.assert_equal(2, result_cw.board[2][1], "capture white piece")
    assertion.assert_equal(-2, result_cb.board[2][3], "capture black piece")    

    # =================================
    # Test move causing piece to be freed.
    result_cw.player = not result_cw.player
    result_cb.player = not result_cb.player

    # Move both pieces that are capturing another.
    result1 = game.result(result_cw, Action((2, 0), (1, 0)))
    result2 = game.result(result_cw, Action((2, 2), (3, 2)))
    result3 = game.result(result_cb, Action((1, 3), (0, 3)))
    result4 = game.result(result_cb, Action((3, 3), (4, 3)))

    assertion.assert_equal(1, result1.board[2][1], "move west frees captured piece")
    assertion.assert_equal(1, result2.board[2][1], "move east frees captured piece")
    assertion.assert_equal(-1, result3.board[2][3], "move north frees captured piece")
    assertion.assert_equal(-1, result4.board[2][3], "move south frees captured piece")
