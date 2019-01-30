"""
random: Implements a simple AI, that only performs random actions.
"""
from time import sleep
from numpy.random import uniform
from controller.game_ai import GameAI

class Random(GameAI):
    def execute_action(self, state):
        super.__doc__
        actions = self.game.actions(state)
        index = int(uniform(0, len(actions)))
        chosen = actions[index]

        print("Action taken: {}".format(chosen))
        return self.game.result(state, chosen)
    
    def __str__(self):
        return "Random Moves Algorithm"
