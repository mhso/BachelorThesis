from testing import assertion
from testing import test_latrunculi
from testing import test_minimax

test_latrunculi.run_tests()
test_minimax.run_tests()

print("Tests Run: {}".format(assertion.PASSED + assertion.FAILED))
print("Passed: {}".format(assertion.PASSED))
print("Failed: {}".format(assertion.FAILED))
