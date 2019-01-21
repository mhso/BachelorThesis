from testing import assertion
from controller.latrunculi import Latrunculi

def run_tests():
    print("-=-=-=- LATRUNCULI GAME TESTS -=-=-=-")
    # Test initial board setup.

    # Test correct board size.
    TEST_SIZE = 8
    GAME = Latrunculi(TEST_SIZE)
    state = GAME.start_state()
    assertion.assert_equal(TEST_SIZE, state.board.shape[1], "correct board width")
    assertion.assert_equal(TEST_SIZE, state.board.shape[0], "correct board height")

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
    GAME = Latrunculi(8, 432)
    state = GAME.start_state()
    num_white = (state.board == 1).sum()
    num_black = (state.board == -1).sum()

    assertion.assert_equal(16, num_black, "number of black pieces random")
    assertion.assert_equal(16, num_white, "number of white pieces random")

    # =================================
    # Test initial player turn is white.
    assertion.assert_true(GAME.player(state), "initial player turn")

    # =================================
    # Test terminal state.
