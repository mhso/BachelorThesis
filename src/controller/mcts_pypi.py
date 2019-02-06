"""
------------------------------------
mcts: Monte Carlo Tree Search from pypi.
With pip: pip install mcts
------------------------------------
"""
import numpy as np
from controller.game_ai import GameAI
from view.log import log
from mcts import mcts as mcts_pypi

class State2():
    game = None
    state = None

    def __init__(self, game, state):
        self.game = game
        self.state = state

    def getPossibleActions(self):
        return self.game.actions(self.state)

    def takeAction(self, action):
        return State2(self.game, self.game.result(self.state, action))

    def isTerminal(self):
        return self.game.terminal_test(self.state)

    def getReward(self):
        return self.game.utility(self.state, self.state.player)

class MCTS_PYPI(GameAI):
    mcts = None
    game = None
    def __init__(self, game, playouts=None):
        self.mcts = mcts_pypi(timeLimit=2000)
        self.game = game

    def execute_action(self, state):
        super.__doc__
        new_state = State2(self.game, state)
        
        chosen = self.mcts.search(initialState=new_state)

        print("MCTS_PYPI action: {}".format(chosen))
        return self.game.result(new_state.state, chosen)
    
    def __str__(self):
        return "Random Moves Algorithm"
