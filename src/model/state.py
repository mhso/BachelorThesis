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

class Action:
    source = 0, 0
    dest = 0, 0

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

    def numeric(self):
        """
        Return unique numeric ID of Action.
        Used in MCTS
        """
        x1, y1 = self.source
        x2, y2 = self.dest
        return int(str(x1)+str(y1)+str(x2)+str(y2))
