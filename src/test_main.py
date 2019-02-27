from testing import assertion
from testing import test_latrunculi
from testing import test_cnnct_four
from testing import test_minimax
from testing import test_mcts
from testing import test_misc

GREEN = "\033[1;32;40m"
YELLOW = "\033[0;33;40m"
RED = "\033[1;31;40m"
RESET = "\033[0;37;40m"

print("{}-=-=-=- LATRUNCULI GAME TESTS -=-=-=-{}".format(YELLOW, RESET))
test_latrunculi.run_tests()
print("{}-=-=-=-=- CONNECT FOUR TESTS -=-=-=-=-{}".format(YELLOW, RESET))
test_cnnct_four.run_tests()
print("{}-=-=-=-=-=- MINIMAX TESTS -=-=-=-=-=-{}".format(YELLOW, RESET))
test_minimax.run_tests()
print("{}-=-=-=-=-=-=- MCTS TESTS -=-=-=-=-=-=-{}".format(YELLOW, RESET))
#test_mcts.run_tests()
print("{}-=-=-=-=- MISCELLANEOUS TESTS -=-=-=-{}".format(YELLOW, RESET))
test_misc.run_tests()

print("===============================================")
print("Tests Run: {}".format(assertion.PASSED + assertion.FAILED))
print("{}Passed: {}".format(GREEN, assertion.PASSED))
print("{}Failed: {}{}".format(RED, assertion.FAILED, RESET))
