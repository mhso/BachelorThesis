import sys
from testing import assertion
from testing import test_latrunculi_vs_latrunculi_ne
GREEN = "\033[1;32;40m"
YELLOW = "\033[0;33;40m"
RED = "\033[1;31;40m"
RESET = "\033[0;37;40m"

args = sys.argv

test_iterations = int(args[1])

print("\n{}-=-=-=- LATRUNCULI VS LATRUNCULI_NE GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
for i in range(1, test_iterations+1):
    print("Test iteration {}/{} ".format(i, test_iterations))
    test_latrunculi_vs_latrunculi_ne.run_iteration_timing_l_vs_l_ne_test()

