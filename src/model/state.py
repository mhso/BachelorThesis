class State:
    board = []
    player = True
    pieces = []

    def __init__(self, board, player, pieces=None):
        self.board = board
        self.player = player
        self.pieces = pieces

    def change_piece(self, y, x, new_y, new_x):
        if new_y is None:
            self.pieces.remove((y, x))
        else:
            for i, (py, px) in enumerate(self.pieces):
                if py == y and px == x:
                    self.pieces[i] = (new_y, new_x)
                    break

    def count_pieces(self):
        """
        Debug method for returning number of white
        and black pieces on the board.
        """
        white_pieces = (self.board == 1).sum()
        black_pieces = (self.board == -1).sum()
        return white_pieces, black_pieces

    def str_player(self):
        """
        Debug method for returning a string
        representation of which player has the turn.
        """
        return "White" if self.player else "Black"

    def __str__(self):
        white_pieces, black_pieces = self.count_pieces()
        return "<State: \nPlayer turn = {}\nWhite pieces = {}\nBlack pieces = {}\nBoard =\n{}\n>".format(
            self.str_player(), white_pieces, black_pieces, self.board)

    def stringify(self):
        return ("1" if self.player else "0") + ("".join([str(p) for p in self.board.ravel()]))

class Action:
    source = 0, 0
    dest = 0, 0

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

    def __eq__(self, other):
        if not self or not other:
            return not self and not other
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
        return "<Action: source({}), dest({})>".format(self.source, self.dest)

    def __repr__(self):
        return self.__str__()
