from testing import assertion
from testing import test_latrunculi
from testing import test_minimax
from testing import test_mcts
from testing import test_misc

test_latrunculi.run_tests()
test_minimax.run_tests()
test_mcts.run_tests()
test_misc.run_tests()

print("===============================================")
print("Tests Run: {}".format(assertion.PASSED + assertion.FAILED))
print("\033[1;32;40mPassed: {}".format(assertion.PASSED))
print("\033[1;31;40mFailed: \033[1;31;40m{}\033[0;37;40m".format(assertion.FAILED))