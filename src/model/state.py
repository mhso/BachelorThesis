class State:
    board = []
    player = True

    def __init__(self, board, player):
        self.board = board
        self.player = player

    def __str__(self):
        player = "White" if self.player else "Black"
        white_pieces = (self.board == 1).sum()
        black_pieces = (self.board == -1).sum()
        return "[State: \nPlayer turn = {}\nWhite pieces = {}\nBlack pieces = {}\nBoard =\n{}\n]".format(
            player, white_pieces, black_pieces, self.board)

    def stringify(self):
        return ("1" if self.player else "0") + ("".join([str(p) for p in self.board.ravel()]))

class Action:
    source = 0, 0
    dest = 0, 0

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

    def __eq__(self, other):
        return self.source == other.source and self.dest == other.dest

    def __hash__(self):
        return hash(str(self))

    def numeric(self):
        """
        Return unique numeric ID of Action.
        Used in MCTS
        """
        x1, y1 = self.source
        x2, y2 = self.dest
        return int(str(x1)+str(y1)+str(x2)+str(y2))

    def __str__(self):
        return "[Action: source({}), dest({})]".format(self.source, self.dest)
