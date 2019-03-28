from sys import argv
from testing import assertion
from testing import test_latrunculi
from testing import test_cnnct_four
from testing import test_othello
from testing import test_minimax
from testing import test_mcts
from testing import test_misc
from testing import test_network

GREEN = "\033[1;32;40m"
YELLOW = "\033[0;33;40m"
RED = "\033[1;31;40m"
RESET = "\033[0;37;40m"

MODULES = {"latrunculi": test_latrunculi,
           "connect_four": test_cnnct_four,
           "othello": test_othello,
           "minimax": test_minimax,
           "mcts": test_mcts,
           "network": test_network,
           "misc": test_misc}

if len(argv) == 1:
    for mod in MODULES:
        print("{}-=-=-=- {} GAME TESTS -=-=-=-{}".format(YELLOW, mod.upper(), RESET))
        MODULES[mod].run_tests()
else:
    MODULES[argv[1]].run_tests()

print("===============================================")
print("Tests Run: {}".format(assertion.PASSED + assertion.FAILED))
print("{}Passed: {}".format(GREEN, assertion.PASSED))
print("{}Failed: {}{}".format(RED, assertion.FAILED, RESET))
