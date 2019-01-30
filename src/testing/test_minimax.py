from testing import assertion
from controller.minimax import Minimax
from controller.latrunculi import Latrunculi

def run_tests():
    print("-=-=-=- MINIMAX TESTS -=-=-=-")
    # Test board evaluation function.
    game = Latrunculi(8)
    minimax = Minimax(game)
    state = game.start_state()

    state.board[0][:2] = 0 # Simulate black losing 2 pieces.
    eval_w = minimax.evaluate_board(state)
    state.player = not state.player # Simulate black having the turn.
    eval_b = minimax.evaluate_board(state)

    assertion.assert_equal(2, eval_w, "evaluate board positive")
    assertion.assert_equal(-2, eval_b, "evaluate board negative")

    # =================================
