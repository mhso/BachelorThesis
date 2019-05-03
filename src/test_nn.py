from model.neural import NeuralNetwork
from controller.othello import Othello
from config import Config
import numpy as np

game = Othello(8)
state1 = game.start_state()
state2 = game.result(state1, game.actions(state1)[0])
Config.CONV_FILTERS = 256

network = NeuralNetwork(game)
network.save_as_image()
image = game.structure_data(state1)
image2 = game.structure_data(state2)
policy, value = network.evaluate(game.structure_data(state1))
print(f"Value white: {value}")
policy, value = network.evaluate(game.structure_data(state2))
print(f"Value black: {value}")
mapstuff = game.map_actions(game.actions(state2), (policy[0][0], policy[1][0]))
