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
    # Check if castling is possible.
    if player > 0:
        if (y, x) == (7, 4):
            if board[7, 0] == 3 and board[7, 1] == 0 and board[7, 2] == 0 and board[7, 3] == 0:
                actions.append((y, x, 7, 2))
            if board[7, 7] == 3 and board[7, 5] == 0 and board[7, 6] == 0:
                actions.append((y, x, 7, 6))
    else:
        if (y, x) == (0, 4):
            if board[0, 0] == -3 and board[0, 1] == 0 and board[0, 2] == 0 and board[0, 3] == 0:
                actions.append((y, x, 0, 2))
            if board[0, 7] == -3 and board[0, 5] == 0 and board[0, 6] == 0:
                actions.append((y, x, 0, 6))
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
    y, x = pos
    # Check for moves.
    if (((player < 0 and y == 1) or (player > 0 and y == size - 2)) and
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
def filter_actions(pieces, board, player, size, actions):
    illegal_actions = []
    # Remove actions that would lead to a check.
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
    filtered = filter_actions(pieces, board, player, size, actions)
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
        return -1 if len(checking) > 0 else 42 # I am so sorry.

    # See whether given player is checking the opponent,
    # and whether the opponent can prevent checkmate.
    king_y, king_x = find_piece(pieces, board, -2*player)
    checking = pieces_checking(actions_player, king_y, king_x)
    return 1 if len(checking) > 0 and len(opp_actions) == 0 else 0

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
        board[7, 4] = Chess.PIDS["KI"]
        board[0, 4] = -Chess.PIDS["KI"]
        board[7, 0] = Chess.PIDS["R"]
        board[7, 7] = Chess.PIDS["R"]
        board[0, 7] = -Chess.PIDS["R"]
        board[0, 0] = -Chess.PIDS["R"]
        board[7, 5] = Chess.PIDS["B"]
        board[1, 1] = Chess.PIDS["P"]
        board[6, 2] = -Chess.PIDS["P"]
        pieces = [(7, 4), (0, 4), (7, 0), (7, 7), (0, 7), (0, 0), (7, 5), (1, 1), (6, 2)]
        return board, pieces

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

    def handle_pawn_promotion(self, board, dest):
        y_s, x_s = dest
        if board[y_s, x_s] == self.PIDS["P"]:
            if y_s == 0:
                board[y_s, x_s] = self.PIDS["Q"]
        elif board[y_s, x_s] == -self.PIDS["P"]:
            if y_s == 7:
                board[y_s, x_s] = -self.PIDS["Q"]

    def handle_castling(self, board, source, dest):
        y_s, x_s = source
        y_d, x_d = dest
        castle_src, castle_dest = None, None
        if board[y_s, x_s] == self.PIDS["KI"] and (y_s, x_s) == (7, 4):
            if (y_d, x_d) == (7, 2):
                castle_src = (7, 0)
                castle_dest = (7, 3)
            elif (y_d, x_d) == (7, 6):
                castle_src = (7, 7)
                castle_dest = (7, 5)
        elif board[y_s, x_s] == -self.PIDS["KI"] and (y_s, x_s) == (0, 4):
            if (y_d, x_d) == (0, 2):
                castle_src = (0, 0)
                castle_dest = (0, 3)
            elif (y_d, x_d) == (0, 6):
                castle_src = (0, 7)
                castle_dest = (0, 5)
        if castle_src is not None:
            c_ys, c_xs = castle_src
            c_yd, c_xd = castle_dest
            return c_ys, c_xs, c_yd, c_xd
        return None

    def result(self, state, action):
        super.__doc__
        # Move pieces and create new state.
        copy_board = np.copy(state.board)
        copy_pieces = [pos for pos in state.pieces]
        new_state = State(copy_board, not state.player, copy_pieces)
        new_state.repetitions = state.repetitions
        new_state.repetition_count = state.repetition_count
        new_state.no_progress_count = state.no_progress_count
        y_s, x_s = action.source
        y_d, x_d = action.dest
        copy_board[y_d, x_d] = copy_board[y_s, x_s]
        copy_board[y_s, x_s] = 0
        new_state.change_piece(y_s, x_s, y_d, x_d)
        new_state.repetitions.append(copy_pieces)
        if len(new_state.repetitions) == 6:
            new_state.repetitions.pop(0)

        # See if the move is equal to castling.
        castle_coords = self.handle_castling(state.board, action.source, action.dest)
        if castle_coords is not None:
            c_ys, c_xs, c_yd, c_xd = castle_coords
            new_state.change_piece(c_ys, c_xs, c_yd, c_xd)
            copy_board[c_yd, c_xd] = copy_board[c_ys, c_xs]
            copy_board[c_ys, c_xs] = 0

        # See if a pawn should be promoted.
        self.handle_pawn_promotion(copy_board, action.dest)

        # See if progress has been made (ie. a piece was captured).
        p_w_before, p_b_before = state.count_pieces()
        p_w_now, p_b_now = new_state.count_pieces()
        piece_diff = (p_w_before + p_b_before) - (p_w_now + p_b_now)
        new_state.no_progress_count = new_state.no_progress_count + 1 if piece_diff == 0 else 0
        # Calculate if new state is repetition.
        if len(new_state.repetitions) == 5 and new_state.repetitions[-1] == new_state.repetitions[0]:
            new_state.repetition_count += 1
        else:
            new_state.repetition_count = 0
        return new_state

    def terminal_test(self, state):
        super.__doc__
        if state.repetition_count >= 13 or state.no_progress_count >= 30:
            return True
        player = 1 if self.player(state) else -1
        return terminal_test_fast(state.pieces, state.board, player, self.size)

    def utility(self, state, player):
        super.__doc__
        player_num = 1 if player else -1
        return utility_fast(state.pieces, state.board, player_num, self.size)

    def structure_data(self, state):
        super.__doc__
        pos_pieces = []
        neg_pieces = []
        for i in range(1, 7):
            pos = np.where(state.board == i, state.board, np.zeros((self.size, self.size), dtype="b"))
            pos[pos == i] = 1
            pos_pieces.append(pos)
            neg = np.where(state.board == -i, state.board, np.zeros((self.size, self.size), dtype="b"))
            neg[neg == -i] = 1
            neg_pieces.append(neg)
        
        piece_list = []
        if state.player:
            pos_pieces.extend(neg_pieces)
            piece_list = pos_pieces
        else:
            neg_pieces.extend(pos_pieces)
            piece_list = neg_pieces

        for _ in range(4):
            # Padding
            piece_list.append(np.zeros((self.size, self.size), dtype="b"))
        return np.array(piece_list, dtype="float32")

    def map_actions(self, actions, logits):
        super.__doc__
        action_map = dict()
        policy_sum = 0
        if actions == [None]:
            action_map[None] = 1
            return action_map
        for action in actions:
            y1, x1 = action.source
            moves = logits[y1, x1]
            y2, x2 = action.dest
            dest = y2 * self.size + x2
            logit = 0
            # Action equals a piece being moved.
            logit = moves[y2 * self.size + x2]
            logit = np.exp(logit)
            action_map[action] = logit
            policy_sum += logit

        for action, policy in action_map.items():
            action_map[action] = policy/policy_sum if policy_sum else 0

        return action_map

    def map_visits(self, visits):
        super.__doc__
        policies = np.zeros((self.size, self.size, self.size*self.size), dtype="float32")
        for a, p in visits.items():
            if a is None:
                continue
            y1, x1 = a.source
            moves = policies[y1, x1]
            y2, x2 = a.dest
            # Action equals a piece being moved.
            moves[y2 * self.size + x2] = p

        return policies
