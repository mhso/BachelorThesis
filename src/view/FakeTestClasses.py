import numpy as np

####################################################################
# Tempory variables for testing
# board = np.array([[0,0,-1,-1,0,0,0,0],[-1,0,0,0,0,0,0,0],[1,0,-1,0,1,0,0,0],[1,0,0,0,0,0,-1,1],[0,1,0,0,0,0,0,-2],[0,0,0,0,-1,0,0,1],[0,0,0,0,0,0,0,1],[0,-1,0,-1,2,-1,0,0]])
# currentPlayer = 1

class Action:
    source = 0, 0
    dest = 0, 0

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

class State:
    board = []
    player = True

    def __init__(self, board, player):
        self.board = board
        self.player = player

    def __str__(self):
        player = "White" if self.player else "Black"
        return "[State: \nPlayer turn = " + player + "\nBoard =\n" + str(self.board) + "\n]"

    def numeric(self):
        return hash(str(self.board))

class TestGame:

    actionslist = []

    def start_state(self):
        """
        Returns starting state for the game.
        """
        board      = np.array([[0,0,-1,-1,0,0,0,0],
                                            [-1,0,0,0,0,0,0,0],
                                            [1,0,-1,0,1,0,0,0],
                                            [1,0,0,0,0,0,-1,1],
                                            [0,1,0,0,0,0,0,-2],
                                            [0,0,0,0,-1,0,0,1],
                                            [0,0,0,0,0,0,0,1],
                                            [0,-1,0,-1,2,-1,0,0]])
        player = 1

        return State(board, player)

    def player(self, state):
        """
        Returns who’s turn it is given a state. True for white, False for black.
        """
        pass

    def actions(self, state):
        """
        Return list of legal moves for the given state.
        """
        actionsList = [Action((2,0),(2,1)),
                            Action((2,4),(1,4)), Action((2,4),(2,3)), Action((2,4),(2,5)), Action((2,4),(3,4)),
                            Action((3,0),(3,1)), Action((3,0),(4,0)),
                            Action((3,7),(2,7)),
                            Action((4,1),(3,1)), Action((4,1),(4,0)), Action((4,1),(4,2)), Action((4,1),(5,1)),
                            Action((5,7),(5,6)),
                            Action((6,7),(6,6)), Action((6,7),(7,7))
                            ]
        return actionsList

    def result(self, state, action):
        """
        Returns the state that results from doing action 'a' in state 's'.
        """
        board      = np.array([[0,0,-1,-1,0,0,0,0],
                                    [-1,0,0,0,0,0,0,0],
                                    [1,0,-1,0,1,0,0,0],
                                    [1,0,0,0,0,0,-1,1],
                                    [0,1,0,0,0,0,0,-2],
                                    [0,0,0,0,-1,0,0,1],
                                    [0,0,0,0,0,0,0,1],
                                    [0,-1,0,-1,2,-1,0,0]])

        return State(board, 1)

    def terminal_test(self, state):
        """
        Return True if the given state is a terminal state, meaning that the game is over, False otherwise.
        """
        pass


    def utility(self, state, player):
        """
        If the given player has lost, return 0, else return 1
        """

####################################################################