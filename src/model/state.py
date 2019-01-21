class State:
    board = []
    turn = True

    def __init__(self, board, turn):
        self.board = board
        self.turn = turn

    def __str__(self):
        turn = "White" if self.turn else "Black"
        return "[State: \nTurn = " + turn + "\nBoard =\n" + str(self.board) + "\n]"

class Action:
    source = 0, 0
    dest = 0, 0