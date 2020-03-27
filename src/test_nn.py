from model.neural import NeuralNetwork
from controller.othello import Othello
from config import Config
import numpy as np

game = Othello(8)
state1 = game.start_state()
state2 = game.result(state1, game.actions(state1)[0])
Config.CONV_FILTERS = 256

network = NeuralNetwork(game)

copy = network.copy_model(game)

new_network = NeuralNetwork(game, copy)

#network.save_as_image()
image = game.structure_data(state1)
image2 = game.structure_data(state2)
policy, value = network.evaluate(game.structure_data(state1))
policy2, value2 = new_network.evaluate(game.structure_data(state1))
print(f"Value white: {value}")
print(f"Value white2: {value2}")
policy, value = network.evaluate(game.structure_data(state2))
polic2y, value2 = new_network.evaluate(game.structure_data(state2))
print(f"Value black: {value}")
print(f"Value black2: {value2}")
