from model.neural import NeuralNetwork
from controller.latrunculi import Latrunculi
import numpy as np

game = Latrunculi(4, 42)
state1 = game.start_state()
state2 = game.result(state1, game.actions(state1)[0])

network = NeuralNetwork()
#network.save_as_image()
policy, value = network.evaluate(game.structure_data(state1))

mapstuff = game.map_logits(game.actions(state1), policy)
