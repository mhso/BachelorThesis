"""
human: Represents a person playing the game.
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
        self.gui.add_action_listener(self)
        while self.state is None and self.gui.active:
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
