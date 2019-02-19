from model.neural import NeuralNetwork
from controller.latrunculi import Latrunculi
import numpy as np

game = Latrunculi(4, 42)
state1 = game.start_state()
state2 = game.result(state1, game.actions(state1)[0])

network = NeuralNetwork()
network.save_as_image()
predict = network.evaluate(np.array([game.structure_data(state1), game.structure_data(state2)]))

print(predict)
