from model.storage import NetworkStorage
from testing import assertion
from model.neural import NeuralNetwork
from controller.othello import Othello

def run_tests():
    game = Othello(6)
    storage = NetworkStorage()
    model = storage.load_network_from_file(None, type(game).__name__)
    network = NeuralNetwork(game, model)
    
    state = game.start_state()
    state.board[:-1, :] = -1
    state.board[-1, :3] = 1

    policies, value = network.evaluate(game.structure_data(state))
    print(policies)
    print(value)
    assertion.assert_true(value > 0, "Network - Value on positive gamestate.")
