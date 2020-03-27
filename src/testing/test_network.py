from model.storage import NetworkStorage
from testing import assertion
from model.neural import NeuralNetwork
from controller.othello import Othello
from numpy import array

def run_tests():
    # Test single input shape.
    game = Othello(6)
    network = NeuralNetwork(game)
    
    state = game.start_state()
    shape = network.shape_input(game.structure_data(state))

    assertion.assert_equal((1, 2, 6, 6), shape.shape, "Single input shape")

    # =================================
    # Test multiple inputs shape.
    state1 = game.start_state()
    state2 = game.result(state1, game.actions(state1)[0])
    state3 = game.result(state1, game.actions(state1)[1])

    in1 = game.structure_data(state1)
    in2 = game.structure_data(state2)
    in3 = game.structure_data(state3)
    shape = network.shape_input(array([in1, in2, in3]))

    assertion.assert_equal((3, 2, 6, 6), shape.shape, "Multiple inputs shape")

    # =================================
    # Test output shape of single input.

    policy, value = network.evaluate(in1)

    assertion.assert_equal((1, 36), policy.shape, "One input - policy shape")
    assertion.assert_equal((1, 1), value.shape, "One input - value shape")

    # =================================
    # Test output shape of multiple inputs.

    policies, values = network.evaluate(array([in1, in2, in3]))
    print(values)

    assertion.assert_equal((3, 36), policies.shape, "Multiple inputs - policy shape")
    assertion.assert_equal((3, 1), values.shape, "Multiple inputs - value shape")
    assertion.assert_equal(policies[0][0], policy[0][0], "Multiple and single policy equal")
    assertion.assert_equal(value[0][0], value[0][0], "Multiple and single value equal")

    # =================================
