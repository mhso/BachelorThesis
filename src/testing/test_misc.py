from testing import assertion
from model.state import Action, State
from controller.latrunculi import Latrunculi

def run_tests():
    print("-=-=-=- MISCELLANEOUS TESTS -=-=-=-")
    # Test Action ID.
    action1 = Action((1, 2), (3, 4))
    action2 = Action((0, 0), (3, 4))

    assertion.assert_equal(1234, action1.numeric(), "action numeric id 1234")
    assertion.assert_equal(34, action2.numeric(), "action numeric id 34")

    # =================================
