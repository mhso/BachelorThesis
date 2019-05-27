import numpy as np
from numba import jit
from controller.game import Game
from model.state import State, Action

@jit(nopython=True)
def is_checked(opp_actions, y, x):
    for (y1, x1, y2, x2) in opp_actions:
        if (y2, x2) == (y, x):
            return True
    return False

@jit(nopython=True)
def pieces_checking(opp_actions, king_y, king_x):
    coords = []
    for (y1, x1, y2, x2) in opp_actions:
        if (y2, x2) == (king_y, king_x):
            coords.append((y1, x1))
    return coords

@jit(nopython=True)
def in_bounds(y, x, size):
    return 0 <= x < size and 0 <= y < size

@jit(nopython=True)
def players_piece(piece, player):
    if player < 0:
        return piece < 0
    else:
        return piece > 0

@jit(nopython=True)
def find_piece(pieces, board, pid):
    for (y, x) in pieces:
        if board[y, x] == pid:
            return (y, x)
    return None

@jit(nopython=True)
def actions_king(pos, board, player, size):
    actions = []
    y, x = pos
    for i in range(y-1, y+2):
        for j in range(x-1, x+2):
            if (in_bounds(i, j, size) and not players_piece(board[i, j], player)):
                actions.append((y, x, i, j))
    return actions

@jit(nopython=True)
def actions_diagonal_nw(pos, board, player, size):
    actions = []
    y, x = pos
    diag_y = y - x if y > x else 0
    j = x - y if x > y else 0
    for i in range(diag_y, size):
        if in_bounds(i, j, size) and not players_piece(board[i, j], player):
            actions.append((y, x, i, j))
        j += 1
        if j >= size:
            break
    return actions

@jit(nopython=True)
def actions_diagonal_ne(pos, board, player, size):
    actions = []
    y, x = pos
    diag_y = y - x if (size-y) > x else size-1
    j = x - y if x > (size-y) else size-1
    for i in range(diag_y, size):
        if in_bounds(i, j, size) and not players_piece(board[i, j], player):
            actions.append((y, x, i, j))
        j += 1
        if j >= size:
            break
    return actions

@jit(nopython=True)
def actions_queen(pos, board, player, size):
    return actions_diagonal_nw(pos, board, player, size)

@jit(nopython=True)
def actions_knight(pos, board, player, size):
    actions = []
    y, x = pos
    vals = [(y-1, x-2), (y-2, x-1), (y-2, x+1), (y-1, x+2),
            (y+1, x+2), (y+2, x+1), (y+2, x-1), (y+1, x-2)]
    for y_dest, x_dest in vals:
        if in_bounds(y_dest, x_dest, size) and not players_piece(board[y_dest, x_dest], player):
            actions.append((y, x, y_dest, x_dest))
    return actions

@jit(nopython=True)
def actions_bishop(pieces, board, player, size):
    pass

@jit(nopython=True)
def actions_rook(pieces, board, player, size):
    pass

@jit(nopython=True)
def actions_pawn(pos, board, player, size):
    actions = []
    if pos is None:
        return actions
    y, x = pos
    if (y, x) == (-1, -1):
        return actions
    # Check for moves.
    if (player < 0 and y == 1) or (player > 0 and y == size - 2):
        # Handle case where pawn can move two squares (at initial position).
        actions.append((y, x, y - (player * 2), x))
    y_dest = y - player
    x_dest = x
    if (in_bounds(y_dest, x_dest, size) and board[y_dest, x_dest] == 0):
        actions.append((y, x, y_dest, x_dest))

    # Check for possible captures.
    # Check left.
    if (in_bounds(y_dest, x_dest, size) and board[y_dest, x_dest] == -player):
        actions.append((y, x, y_dest, x_dest))
    x_dest = x + 1
    # Check right.
    if (in_bounds(y_dest, x_dest, size) and board[y_dest, x_dest] == -player):
        actions.append((y, x, y_dest, x_dest))
    return actions

@jit(nopython=True)
def actions_for_piece(pid, pos, board, player, size):
    if pid == 1:
        return actions_queen(pos, board, player, size)
    if pid == 2:
        return actions_king(pos, board, player, size)
    if pid == 4:
        return actions_knight(pos, board, player, size)
    if pid == 6:
        return actions_pawn(pos, board, player, size)
    return None

@jit(nopython=True)
def actions_fast(pieces, board, player, size, prev_actions):
    action_coords = []
    king_y, king_x = find_piece(pieces, board, player * 2)
    checking_pieces = pieces_checking(prev_actions, king_y, king_x)
    for (y, x) in pieces:
        if players_piece(board[y, x], player):
            pid_abs = abs(board[y, x])
            actions = actions_for_piece(pid_abs, (y, x), board, player, size)
            if actions is not None:
                action_coords.extend(actions)

    illegal_actions = []
    if len(checking_pieces) > 0:
        for y, x in checking_pieces:
            for i, (y1, x1, y2, x2) in enumerate(action_coords):
                old_piece = board[y1, x1]
                board[y2, x2] = board[y1, x1] # Simulate move.
                king_y, king_x = find_piece(pieces, board, player * 2)
                if not players_piece(board[y, x], player):
                    pid = abs(board[y, x])
                    new_actions = actions_for_piece(pid, (y, x), board, -player, size)
                    if actions is not None and is_checked(new_actions, king_y, king_x):
                        illegal_actions.append(i)
                board[y1, x1] = old_piece
    else:
        checking_pieces = pieces_checking(prev_actions, king_y, king_x)
        if len(checking_pieces) > 0:
            for check_y, check_x in checking_pieces:
                for (y_prev_src, x_prev_src, y_prev_dest, x_prev_dest) in prev_actions:
                    if check_y == y_prev_src and check_x == x_prev_src:
                        for i, (y1, x1, y2, x2) in enumerate(action_coords):
                            if y1 == y_prev_dest and x1 == x_prev_dest:
                                illegal_actions.append(i)
    removed = 0
    for index in illegal_actions:
        action_coords.pop(index-removed)
        removed += 1

    return action_coords

class Chess(Game):
    PIDS = {"Q": 1, "KI": 2, "R": 3, "KN": 4, "B": 5, "P": 6}
    curr_actions = [(-1, -1, -1, -1)]
    prev_actions = [(-1, -1, -1, -1)]
    action_type = "dual"

    def __init__(self, size, rand_seed=None):
        super().__init__(size)
        self.num_actions = 4672

    def start_state(self):
        super.__doc__
        board = np.zeros((self.size, self.size), dtype="b")
        board[0, :] = [-self.PIDS["R"], -self.PIDS["KN"], -self.PIDS["B"], -self.PIDS["Q"],
                       -self.PIDS["KI"], -self.PIDS["B"], -self.PIDS["KN"], -self.PIDS["R"]]
        board[1, :] = [-self.PIDS["P"] for _ in range(self.size)]
        board[-1, :] = [self.PIDS["R"], self.PIDS["KN"], self.PIDS["B"], self.PIDS["Q"],
                        self.PIDS["KI"], self.PIDS["B"], self.PIDS["KN"], self.PIDS["R"]]
        board[-2, :] = [self.PIDS["P"] for _ in range(self.size)]
        pieces = [(y, x) for y in range(0, self.size, self.size-1) for x in range(self.size)]
        pieces.extend([(y, x) for y in range(1, self.size-1, self.size-3) for x in range(self.size)])
        
        board[4, 3] = self.PIDS["Q"]
        pieces.append((4, 3))

        return State(board, True, pieces)

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        player_num = 1 if self.player(state) else -1
        actions = actions_fast(state.pieces, state.board, player_num, self.size, self.prev_actions)
        self.curr_actions = actions
        if actions == []:
            self.curr_actions = [(-1, -1, -1, -1)]
            return [None]
        return [Action((y1, x1), (y2, x2)) for y1, x1, y2, x2 in actions]

    def result(self, state, action):
        super.__doc__
        self.prev_actions = self.curr_actions
        return state

    def terminal_test(self, state):
        super.__doc__
        return True

    def utility(self, state, player):
        super.__doc__
        return 0

    def structure_data(self, state):
        super.__doc__
        return []

    def map_actions(self, actions, logits):
        super.__doc__
        return {}

    def map_visits(self, visits):
        super.__doc__
        return []
