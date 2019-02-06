import sys
from testing import assertion
from testing import test_latrunculi
from testing import test_latrunculi_s
from testing import test_latrunculi_ne
from testing import test_cnnct_four
from testing import test_minimax
from testing import test_mcts
from testing import test_misc

GREEN = "\033[1;32;40m"
YELLOW = "\033[0;33;40m"
RED = "\033[1;31;40m"
RESET = "\033[0;37;40m"

args = sys.argv

test_iterations = int(args[1])
times_l = []
times_ne = []
times_cf = []

print("\n{}-=-=-=- LATRUNCULI GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations+1):
    print("Test iteration {}/{} ".format(i, test_iterations))
    time_taken = test_latrunculi.run_iteration_timing_test(log_type="sql")
    times_l.append(time_taken)
print("\n{}-=-=-=- LATRUNCULI_S GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations+1):
    print("Test iteration {}/{} ".format(i, test_iterations))
    time_taken = test_latrunculi_s.run_iteration_timing_test(log_type="sql")
    times_l.append(time_taken)
print("\n{}-=-=-=- LATRUNCULI_NE GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations+1):
    print("Test iteration {}/{} ".format(i, test_iterations))
    time_taken = test_latrunculi_ne.run_iteration_timing_test(log_type=None)
    times_ne.append(time_taken)
print("\n{}-=-=-=-=- CONNECT FOUR TESTS -=-=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations+1):
    print("Test iteration {}/{} ".format(i, test_iterations))
    time_taken = test_cnnct_four.run_iteration_timing_test(log_type=None)
    times_cf.append(time_taken)

print("Average time for Latrunculi: {} s".format(sum(times_l) / len(times_l)))
print("Average time for Latrunculi_ne: {} s".format(sum(times_ne) / len(times_ne)))
print("Average time for Connect Four: {} s".format(sum(times_cf) / len(times_cf)))
