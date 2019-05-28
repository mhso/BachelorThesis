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
def pieces_checking(actions, king_y, king_x):
    coords = []
    for (y1, x1, y2, x2) in actions:
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
    return (-1, -1)

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
    j = x + 1
    for i in range(y + 1, size):
        if in_bounds(i, j, size):
            if board[i, j] == 0:
                actions.append((y, x, i, j))
            else:
                if not players_piece(board[i, j], player):
                    actions.append((y, x, i, j))
                break
        j += 1
        if j >= size:
            break
    j = x - 1
    for i in range(y - 1, -1, -1):
        if in_bounds(i, j, size):
            if board[i, j] == 0:
                actions.append((y, x, i, j))
            else:
                if not players_piece(board[i, j], player):
                    actions.append((y, x, i, j))
                break
        j -= 1
        if j < 0:
            break
    return actions

@jit(nopython=True)
def actions_diagonal_ne(pos, board, player, size):
    actions = []
    y, x = pos
    j = x - 1
    for i in range(y + 1, size):
        if in_bounds(i, j, size):
            if board[i, j] == 0:
                actions.append((y, x, i, j))
            else:
                if not players_piece(board[i, j], player):
                    actions.append((y, x, i, j))
                break
        j -= 1
        if j < 0:
            break
    j = x + 1
    for i in range(y - 1, -1, -1):
        if in_bounds(i, j, size):
            if board[i, j] == 0:
                actions.append((y, x, i, j))
            else:
                if not players_piece(board[i, j], player):
                    actions.append((y, x, i, j))
                break
        j += 1
        if j >= size:
            break
    return actions

@jit(nopython=True)
def actions_vertical(pos, board, player, size):
    actions = []
    y, x = pos
    for i in range(y + 1, size):
        if in_bounds(i, x, size):
            if board[i, x] == 0:
                actions.append((y, x, i, x))
            else:
                if not players_piece(board[i, x], player):
                    actions.append((y, x, i, x))
                break
    for i in range(y - 1, -1, -1):
        if in_bounds(i, x, size):
            if board[i, x] == 0:
                actions.append((y, x, i, x))
            else:
                if not players_piece(board[i, x], player):
                    actions.append((y, x, i, x))
                break
    return actions

@jit(nopython=True)
def actions_horizontal(pos, board, player, size):
    actions = []
    y, x = pos
    for j in range(x + 1, size):
        if in_bounds(y, j, size):
            if board[y, j] == 0:
                actions.append((y, x, y, j))
            else:
                if not players_piece(board[y, j], player):
                    actions.append((y, x, y, j))
                break
    for j in range(x - 1, -1, -1):
        if in_bounds(y, j, size):
            if board[y, j] == 0:
                actions.append((y, x, y, j))
            else:
                if not players_piece(board[y, j], player):
                    actions.append((y, x, y, j))
                break
    return actions

@jit(nopython=True)
def actions_queen(pos, board, player, size):
    actions = actions_vertical(pos, board, player, size)
    actions.extend(actions_horizontal(pos, board, player, size))
    actions.extend(actions_diagonal_nw(pos, board, player, size))
    actions.extend(actions_diagonal_ne(pos, board, player, size))
    return actions

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
def actions_bishop(pos, board, player, size):
    actions = actions_diagonal_nw(pos, board, player, size)
    actions.extend(actions_diagonal_ne(pos, board, player, size))
    return actions

@jit(nopython=True)
def actions_rook(pos, board, player, size):
    actions = actions_vertical(pos, board, player, size)
    actions.extend(actions_horizontal(pos, board, player, size))
    return actions

@jit(nopython=True)
def actions_pawn(pos, board, player, size):
    actions = []
    if pos is None:
        return actions
    y, x = pos
    if (y, x) == (-1, -1):
        return actions
    # Check for moves.
    if (player < 0 and y == 1) or (player > 0 and y == size - 2 and
            not players_piece(board[y - (player * 2), x], player) and
            not players_piece(board[y - player, x], player)):
        # Handle case where pawn can move two squares (at initial position).
        actions.append((y, x, y - (player * 2), x))
    y_dest = y - player
    x_dest = x
    if (in_bounds(y_dest, x_dest, size) and board[y_dest, x_dest] == 0):
        actions.append((y, x, y_dest, x_dest))
    x_dest = x - 1
    # Check for possible captures.
    # Check left.
    if (in_bounds(y_dest, x_dest, size)
            and board[y_dest, x_dest] != 0
            and not players_piece(board[y_dest, x_dest], player)):
        actions.append((y, x, y_dest, x_dest))
    x_dest = x + 1
    # Check right.
    if (in_bounds(y_dest, x_dest, size)
            and board[y_dest, x_dest] != 0
            and not players_piece(board[y_dest, x_dest], player)):
        actions.append((y, x, y_dest, x_dest))
    return actions

@jit(nopython=True)
def actions_for_piece(pid, pos, board, player, size):
    if pid == 1:
        return actions_queen(pos, board, player, size)
    if pid == 2:
        return actions_king(pos, board, player, size)
    if pid == 3:
        return actions_rook(pos, board, player, size)
    if pid == 4:
        return actions_knight(pos, board, player, size)
    if pid == 5:
        return actions_bishop(pos, board, player, size)
    if pid == 6:
        return actions_pawn(pos, board, player, size)
    return None

@jit(nopython=True)
def simulate_move(pieces, board, source, dest):
    copy_b = np.copy(board)
    copy_b[dest] = copy_b[source]
    copy_b[source] = 0
    copy_p = [pos for pos in pieces]
    from_id = -1
    to_id = -1
    for i, pos in enumerate(copy_p):
        if pos == source:
            from_id = i
        elif pos == dest:
            to_id = i
    copy_p[from_id] = dest
    if to_id != -1:
        copy_p.pop(to_id)
    return copy_b, copy_p

@jit(nopython=True)
def filter_actions(pieces, board, player, size, actions, actions_opp):
    king_y, king_x = find_piece(pieces, board, player * 2)
    checking_pieces = pieces_checking(actions_opp, king_y, king_x)

    illegal_actions = []
    if len(checking_pieces) > 0:
        # If we were checked, see if any actions do not resolve this.
        # If so, remove them from the legal actions.
        for i, (y1, x1, y2, x2) in enumerate(actions):
            copy_b, copy_p = simulate_move(pieces, board, (y1, x1), (y2, x2))
            king_y, king_x = find_piece(copy_p, copy_b, player * 2)
            new_actions = calculate_actions(copy_p, copy_b, -player, size)
            if len(pieces_checking(new_actions, king_y, king_x)) > 0:
                illegal_actions.append(i)
    else:
        # If we were NOT checked, but any of the actions will lead to
        # a check, remove these from the legal actions.
        for i, (y1, x1, y2, x2) in enumerate(actions):
            copy_b, copy_p = simulate_move(pieces, board, (y1, x1), (y2, x2))
            king_y, king_x = find_piece(copy_p, copy_b, player * 2)
            new_actions = calculate_actions(copy_p, copy_b, -player, size)
            if len(pieces_checking(new_actions, king_y, king_x)) > 0:
                illegal_actions.append(i)
    removed = 0
    for index in illegal_actions:
        actions.pop(index-removed)
        removed += 1

    return actions

@jit(nopython=True)
def calculate_actions(pieces, board, player, size):
    action_coords = []
    for (y, x) in pieces:
        if players_piece(board[y, x], player):
            pid_abs = abs(board[y, x])
            actions = actions_for_piece(pid_abs, (y, x), board, player, size)
            if actions is not None:
                action_coords.extend(actions)
    return action_coords

@jit(nopython=True)
def actions_fast(pieces, board, player, size):
    actions = calculate_actions(pieces, board, player, size)
    opp_actions = calculate_actions(pieces, board, -player, size)
    filtered = filter_actions(pieces, board, player, size, actions, opp_actions)
    return filtered

@jit(nopython=True)
def terminal_test_fast(pieces, board, player, size):
    return utility_with_remy(pieces, board, player, size) != 0

@jit(nopython=True)
def utility_with_remy(pieces, board, player, size):
    # Check the same, but vice versa.
    actions_player = actions_fast(pieces, board, player, size)
    opp_actions = actions_fast(pieces, board, -player, size)
    king_y, king_x = find_piece(pieces, board, 2*player)
    checking = pieces_checking(opp_actions, king_y, king_x)
    if len(actions_player) == 0:
        return -1 if len(checking) > 1 else 42

    # See whether given player is checking the opponent,
    # and whether the opponent can prevent checkmate.
    king_y, king_x = find_piece(pieces, board, -2*player)
    checking = pieces_checking(actions_player, king_y, king_x)
    return 1 if len(checking) > 1 and len(opp_actions) == 0 else 0 # I am so sorry.

@jit(nopython=True)
def utility_fast(pieces, board, player, size):
    val = utility_with_remy(pieces, board, player, size)
    return 0 if val == 42 else val

class Chess(Game):
    PIDS = {"Q": 1, "KI": 2, "R": 3, "KN": 4, "B": 5, "P": 6}
    action_type = "dual"

    def __init__(self, size, rand_seed=None):
        super().__init__(size)
        self.num_actions = 4672

    def test_setup(self):
        board = np.zeros((self.size, self.size), dtype="b")
        board[4, 2] = -Chess.PIDS["R"]
        board[4, 6] = Chess.PIDS["KI"]
        board[1, 1] = Chess.PIDS["P"]
        board[2, 4] = Chess.PIDS["Q"]
        return board, [(3, 3), (1, 4)]

    def start_state(self):
        super.__doc__
        """
        board = np.zeros((self.size, self.size), dtype="b")
        board[0, :] = [-self.PIDS["R"], -self.PIDS["KN"], -self.PIDS["B"], -self.PIDS["Q"],
                       -self.PIDS["KI"], -self.PIDS["B"], -self.PIDS["KN"], -self.PIDS["R"]]
        board[1, :] = [-self.PIDS["P"] for _ in range(self.size)]
        board[-1, :] = [self.PIDS["R"], self.PIDS["KN"], self.PIDS["B"], self.PIDS["Q"],
                        self.PIDS["KI"], self.PIDS["B"], self.PIDS["KN"], self.PIDS["R"]]
        board[-2, :] = [self.PIDS["P"] for _ in range(self.size)]
        pieces = [(y, x) for y in range(0, self.size, self.size-1) for x in range(self.size)]
        pieces.extend([(y, x) for y in range(1, self.size-1, self.size-3) for x in range(self.size)])
        """
        board = np.zeros((self.size, self.size), dtype="b")
        board[7, 7] = -Chess.PIDS["KI"]

        board[4, 6] = Chess.PIDS["KI"]
        board[7, 5] = Chess.PIDS["B"]
        board[5, 6] = Chess.PIDS["Q"]
        pieces = [(7, 7), (4, 6), (7, 5), (5, 6)]
        #board, pieces = self.test_setup()

        return State(board, True, pieces)

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        player_num = 1 if self.player(state) else -1
        actions = actions_fast(state.pieces, state.board, player_num, self.size)
        if actions == []:
            return [None]
        return [Action((y1, x1), (y2, x2)) for y1, x1, y2, x2 in actions]

    def result(self, state, action):
        super.__doc__
        copy_board = np.copy(state.board)
        copy_pieces = [pos for pos in state.pieces]
        new_state = State(copy_board, not state.player, copy_pieces)
        y_s, x_s = action.source
        y_d, x_d = action.dest
        copy_board[y_d, x_d] = copy_board[y_s, x_s]
        copy_board[y_s, x_s] = 0
        new_state.change_piece(y_s, x_s, y_d, x_d)
        return new_state

    def terminal_test(self, state):
        super.__doc__
        player = 1 if self.player(state) else -1
        return terminal_test_fast(state.pieces, state.board, player, self.size)

    def utility(self, state, player):
        super.__doc__
        player_num = 1 if player else -1
        return utility_fast(state.pieces, state.board, player_num, self.size)

    def structure_data(self, state):
        super.__doc__
        return []

    def map_actions(self, actions, logits):
        super.__doc__
        return {}

    def map_visits(self, visits):
        super.__doc__
        return []
