from numpy.random import uniform
from time import time
import numpy as np
from testing import assertion
from controller.latrunculi import Latrunculi
from model.state import Action
from util.excelUtil import ExcelUtil
from util.sqlUtil import SqlUtil

def run_tests():
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
    # Test piece list is correct.
    pieces_board = []
    it = np.nditer(state.board, flags=["multi_index"])
    while not it.finished:
        y, x = it.multi_index
        if it[0] == 1 or it[0] == -1:
            pieces_board.append((y, x))
        it.iternext()

    assertion.assert_all_equal(pieces_board, state.pieces, "correct pieces in piece list")

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

    assertion.assert_equal(-1, game.utility(state, True), "utility white")
    assertion.assert_equal(1, game.utility(state, False), "utility black")

    # =================================
    # Test available actions for "Chess" formation.
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
    # Test available actions for "random" board.
    game = Latrunculi(6, 5)
    state = game.start_state()
    state.player = not state.player

    legal_moves = [
        Action((0, 1), (1, 1)), Action((0, 2), (1, 2)),
        Action((1, 0), (2, 0)), Action((1, 0), (1, 1)),
        Action((1, 4), (2, 4)), Action((1, 4), (1, 3)), Action((1, 4), (0, 4)),
        Action((1, 5), (2, 5)), Action((1, 5), (1, 3)), Action((2, 1), (1, 1)),
        Action((2, 1), (2, 0)), Action((2, 1), (2, 2)), Action((5, 0), (4, 0)),
        Action((5, 2), (4, 2)), Action((5, 2), (5, 3)), Action((5, 4), (4, 4)),
        Action((5, 4), (5, 3)), Action((5, 4), (5, 5))
    ]

    assertion.assert_all_equal(legal_moves, game.actions(state), "legal random moves white")

    # =================================
    # Test result of action.
    # Test simple move.
    game = Latrunculi(5)
    state = game.start_state()

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
    # Test double jump.
    game = Latrunculi(6, 489)
    state = game.start_state()

    result = game.result(state, Action((4, 1), (4, 5)))
    old_piece = state.board[4][1]
    old_vacant = state.board[4][5]
    new_vacant = result.board[4][1]
    new_piece = result.board[4][5]

    assertion.assert_true(old_piece == new_piece, "double jump move piece moved")
    assertion.assert_true(old_vacant == new_vacant, "double jump move piece absent")

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
    # Test captured piece not being able to move.
    actions = game.actions(result_cw)

    cant_move = True
    for action in actions:
        cant_move = action.source != (2, 1) and cant_move

    assertion.assert_true(cant_move, "captured piece can't move")

    # =================================
    # Test move causing captured piece to be freed.
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

    # =================================
    # Test capture causing captured piece to be freed.
    game = Latrunculi(5, 302)
    state = game.start_state()

    result1 = game.result(state, Action((3, 4), (3, 3))) # Capture black piece.
    result2 = game.result(result1, Action((1, 3), (2, 3))) # Free that piece.

    assertion.assert_equal(-2, result1.board[3][2], "captured black piece for freeing")
    assertion.assert_equal(-1, result2.board[3][2], "free piece by capture")

    # =================================
    # Test potential capture causing move not being possible.
    game = Latrunculi(8, 31)
    state = game.start_state()
    state.player = not state.player

    actions = game.actions(state)

    cant_move = True
    for action in actions:
        cant_move = action.dest != (3, 2) and cant_move

    assertion.assert_true(cant_move, "suicide can't move")

    # =================================
    # Test suicide move, a move that would normally result in capture,
    # but instead captures one of the two enemy pieces.

    # Test south
    game = Latrunculi(8, 42)
    state = game.start_state()
    state.player = not state.player

    exists = Action((6, 1), (7, 1)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move south")

    # =================================
    # Test south again
    game = Latrunculi(8, 107)
    state = game.start_state()
    state.player = not state.player

    exists = Action((3, 2), (4, 2)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move south 2")

    # =================================
    # Test south again again
    game = Latrunculi(8, 75)
    state = game.start_state()

    exists = Action((0, 2), (1, 2)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move south 3")

    # =================================
    # Test west
    game = Latrunculi(8, 96)
    state = game.start_state()

    exists = Action((3, 3), (3, 2)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move west")

    # =================================
    # Test west again
    game = Latrunculi(8, 118)
    state = game.start_state()

    exists = Action((3, 7), (3, 6)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move west 2")

    # =================================
    # Test east
    game = Latrunculi(8, 102)
    state = game.start_state()

    exists = Action((2, 1), (2, 2)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move east")

    # =================================
    # Test east again
    game = Latrunculi(8, 77)
    state = game.start_state()

    exists = Action((1, 1), (1, 2)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move east 2")

    # =================================
    # Test north
    game = Latrunculi(8, 118)
    state = game.start_state()

    exists = Action((6, 3), (5, 3)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move north")

    # =================================
    # Test north again
    game = Latrunculi(8, 70)
    state = game.start_state()

    exists = Action((6, 3), (5, 3)) in game.actions(state)

    assertion.assert_true(exists, "regular suicide move north 2")

    # =================================
    # Test potential capture causign move not being possible.
    game = Latrunculi(8, 69)
    state = game.start_state()
    state.player = not state.player

    exists = Action((1, 2), (3, 2)) in game.actions(state)

    assertion.assert_true(exists, "jump suicide move")

    # =================================
    # Test chump jain being broken, by potential capture.
    new_state = game.result(state, Action((1, 2), (3, 2)))

def run_iteration_timing_test(log_type=None):
    # TEST STUFF
    print("run iteration timing test Latrunculi")
    game = Latrunculi(8, 42)
    state = game.start_state()

    time_b = time()

    counter = 0
    while counter < 3000:
        actions = game.actions(state)
        action = actions[int(uniform(0, len(actions)))]
        result = game.result(state, action)
        counter += 1

    time_taken = time() - time_b
    print("Time taken to play out game: {} s".format(time_taken))
    print("Iterations: {}".format(counter))

    if log_type == 'excel':
        # Appending results to standard excel file "test_results.xlsx"
        row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "Latrunculi", counter, (time() - time_b))
        ExcelUtil.excel_append_row(row)
    elif log_type == 'sql':
        row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "Latrunculi", counter, (time() - time_b))
        sql_conn = SqlUtil.connect()
        SqlUtil.test_iteration_timing_insert_row(sql_conn, row)

    return time_taken
