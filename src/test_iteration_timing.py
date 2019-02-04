import sys
from testing import assertion
from testing import test_latrunculi
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

test_iterations = int(args[1])+1


print("\n{}-=-=-=- LATRUNCULI GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations):
    print("Test iteration {}/{} ".format(i, test_iterations))
    test_latrunculi.run_iteration_timing_test()
print("\n{}-=-=-=- LATRUNCULI GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations):
    print("Test iteration {}/{} ".format(i, test_iterations))
    test_latrunculi_ne.run_iteration_timing_test()
print("\n{}-=-=-=-=- CONNECT FOUR TESTS -=-=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations):
    print("Test iteration {}/{} ".format(i, test_iterations))
    test_cnnct_four.run_iteration_timing_test()

print("===============================================")
print("Tests Run: {}".format(assertion.PASSED + assertion.FAILED))
print("{}Passed: {}".format(GREEN, assertion.PASSED))
print("{}Failed: {}{}".format(RED, assertion.FAILED, RESET))
