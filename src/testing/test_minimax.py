from testing import assertion
from controller.minimax import Minimax
from controller.minimax_cf import Minimax_CF
from controller.latrunculi import Latrunculi
from controller.connect_four import Connect_Four

def run_tests():
    # Test board evaluation function.
    game = Latrunculi(8)
    minimax = Minimax(game)
    state = game.start_state()

    state.board[0][:2] = -2 # Simulate black losing 2 pieces.
    eval_w = minimax.evaluate_board(state, 1)
    state.player = not state.player # Simulate black having the turn.
    eval_b = minimax.evaluate_board(state, 1)

    assertion.assert_equal(4, eval_w, "latrunculi evaluate board positive")
    assertion.assert_equal(-14, eval_b, "latrunculi evaluate board negative")

    # =================================
    game = Connect_Four(7)
    minimax = Minimax_CF(game)
    state = game.start_state()

    state.board[3:6, 1] = -1
    state.board[4:6, 2] = 1
    
    eval_w = minimax.evaluate_board(state, 0)
    state.player = not state.player # Simulate black having the turn.
    eval_b = minimax.evaluate_board(state, 0)

    assertion.assert_equal(3, eval_w, "connect four evaluate board positive")
    assertion.assert_equal(-3, eval_b, "connect four evaluate board negative")
