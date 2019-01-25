"""
random: Implements Minimax with Alpha-Beta pruning for playing a game.
"""
from controller.game_ai import GameAI
from numpy.random import uniform

class Random(GameAI):
    def execute_action(self, state):
        super.__doc__
        actions = self.game.actions(state)
        index = int(uniform(0, len(actions)))
        print(index)
        print(len(actions))
        chosen = actions[index]

        print("Action taken: {}".format(chosen))
        return self.game.result(state, chosen)
    
    def __str__(self):
        return "Random Moves Algorithm"
