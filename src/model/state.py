class State:
    board = []
    player = True

    def __init__(self, board, player):
        self.board = board
        self.player = player

    def __str__(self):
        player = "White" if self.player else "Black"
        return "[State: \nPlayer turn = " + player + "\nBoard =\n" + str(self.board) + "\n]"

class Action:
    source = 0, 0
    dest = 0, 0
