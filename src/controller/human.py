"""
random: Implements Minimax with Alpha-Beta pruning for playing a game.
"""
from time import sleep
from controller.game_ai import GameAI
from view.log import log

class Human(GameAI):
    gui = None
    state = None

    def execute_action(self, state):
        super.__doc__
        
        log("Waiting for player input...")
        self.state = None
        self.gui.listen_for_action(self)
        while self.state is None:
            sleep(0.1)
        return self.state

    def action_made(self, state):
        """
        Called when the human player has selected
        a move/action.
        """
        self.state = state

    def __str__(self):
        return "Human Player"
