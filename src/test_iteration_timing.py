import sys
from testing import assertion
from testing import test_latrunculi
from testing import test_cnnct_four
from testing import test_minimax
from testing import test_mcts
from testing import test_misc
from testing import test_chess

GREEN = "\033[1;32;40m"
YELLOW = "\033[0;33;40m"
RED = "\033[1;31;40m"
RESET = "\033[0;37;40m"

args = sys.argv

test_iterations = int(args[1])
games_to_test = None
if len(args) > 2:
    games_to_test = args[2]
times_l = []
times_ne = []
times_cf = []
times_c = []
test_l = games_to_test is None or games_to_test == "latrunculi"
test_cf =  games_to_test is None or games_to_test == "connect4"
test_c =  games_to_test is None or games_to_test == "chess"

if test_l:
    print("\n{}-=-=-=- LATRUNCULI GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
    for i in range(1, test_iterations+2):
        print("Test iteration {}/{} ".format(i, test_iterations))
        time_taken = test_latrunculi.run_iteration_timing_test()
        if i > 1:
            times_l.append(time_taken)
if test_cf:
    print("\n{}-=-=-=-=- CONNECT FOUR TESTS -=-=-=-=-{}".format(YELLOW, RESET))
    for i in range(1, test_iterations+1):
        print("Test iteration {}/{} ".format(i, test_iterations))
        time_taken = test_cnnct_four.run_iteration_timing_test(log_type=None)
        times_cf.append(time_taken)
if test_c:
    print("\n{}-=-=-=-=- CHESS TEST -=-=-=-=-{}".format(YELLOW, RESET))
    for i in range(1, test_iterations+2):
        print("Test iteration {}/{} ".format(i, test_iterations))
        time_taken = test_chess.run_iteration_timing_test(log_type=None)
        if i > 1:
            times_c.append(time_taken)

if test_l:
    print("Average time for Latrunculi: {} s".format(sum(times_l) / len(times_l)))
if test_cf:
    print("Average time for Connect Four: {} s".format(sum(times_cf) / len(times_cf)))
if test_c:
    print("Average time for Chess: {} s".format(sum(times_c) / len(times_c)))
