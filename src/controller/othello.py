import numpy as np
from numba import jit
from controller.game import Game
from model.state import State, Action

@jit(nopython=True)
def capture_in_dir(board, player, x, y, i, j, size):
    """
    captures pieces in a certain direction
    """
    captures = 1
    other_player = -player
    xc = x+i
    yc = y+j
    while size > xc >= 0 and size > yc >= 0 and board[yc][xc] == other_player:
        xc += i
        yc += j
        captures += 1
    if captures and size > xc >= 0 and size > yc >= 0 and board[yc][xc] == player:
        return captures
    return 0

@jit(nopython=True)
def action_at(board, y, x, size, player, other):
    action_list = []
    if board[y][x] == other:
        for j in range(-1, 2):
            for i in range(-1, 2):
                pos_x, pos_y = x-i, y-j
                if (size > pos_x >= 0 and size > pos_y >= 0 and
                        board[pos_y][pos_x] == 0 and capture_in_dir(board, player, x, y, i, j, size)):
                    action_list.append((pos_y, pos_x))
    return action_list

@jit(nopython=True)
def result(arr, y, x, size, player):
    """
    logic for calculating result, using jit compilation
    """
    captures = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            captures = capture_in_dir(arr, player, x, y, i, j, size)
            for k in range(1, captures+1):
                arr[y+j*k, x+i*k] = player
    arr[y][x] = player
    return arr

@jit(nopython=True)
def utility(board, pieces, player):
    """
    logic for calculating utility value of a board, using jit compilation
    """
    player_num = 1 if player else -1
    other_num = -player_num
    pieces_player, pieces_opp = 0, 0
    for y, x in pieces:
        piece = board[y][x]
        if piece == player_num:
            pieces_player += 1
        elif piece == other_num:
            pieces_opp += 1
    diff = pieces_player - pieces_opp
    return 1 if diff > 0 else -1 if diff else 0

class Othello(Game):

    def __init__(self, size, rand_seed=None):
        Game.__init__(self, size)
        self.num_actions = self.size * self.size

    def start_state(self):
        super.__doc__
        board = np.zeros((self.size, self.size), dtype="b")
        half = self.size // 2
        board[half][half-1] = 1
        board[half-1][half] = 1
        board[half][half] = -1
        board[half-1][half-1] = -1
        pieces = [(half, half-1), (half-1, half), (half, half), (half-1, half-1)]
        return State(board, True, pieces=pieces)

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        action_list = []
        board = state.board
        player_num = 1 if state.player else -1
        other_num = -player_num
        for y, x in state.pieces:
            action_list.extend(action_at(board, y, x, self.size, player_num, other_num))
        if action_list == []:
            return [None]
        return [Action(None, (y, x)) for (y, x) in action_list]

    def result(self, state, action):
        super.__doc__
        copy_arr = np.copy(state.board)
        new_state = State(copy_arr, not state.player, [p for p in state.pieces])
        if not action:
            return new_state
        player_num = 1 if state.player else -1
        y, x = action.dest
        result(copy_arr, y, x, self.size, player_num)
        new_state.pieces.append((y, x))
        return new_state

    def terminal_test(self, state):
        super.__doc__
        actions_cp = self.actions(state)
        if actions_cp == [None]:
            state.player = not state.player
            actions_op = self.actions(state)
            state.player = not state.player
            if actions_op == [None]:
                return True
        return False

    def utility(self, state, player):
        super.__doc__
        return utility(state.board, state.pieces, player)

    def structure_data(self, state):
        super.__doc__
        pos_pieces = np.where(state.board == 1, state.board, np.zeros((self.size, self.size), dtype="b"))
        neg_pieces = -np.where(state.board == -1, state.board, np.zeros((self.size, self.size), dtype="b"))

        # Structure data as a 4x4x2 stack.
        if state.player:
            return np.array([pos_pieces, neg_pieces], dtype="float32")
        else:
            return np.array([neg_pieces, pos_pieces], dtype="float32")

    def map_actions(self, actions, logits):
        super.__doc__
        action_map = dict()
        policy_sum = 0
        if actions == [None]:
            action_map[None] = 1
            return action_map
        for action in actions:
            y, x = action.dest
            logit = np.exp(logits[y * self.size + x])
            action_map[action] = logit
            policy_sum += logit
        for action, policy in action_map.items():
            action_map[action] = policy/policy_sum if policy_sum else 0
        return action_map

    def map_visits(self, visits):
        super.__doc__
        policies = np.zeros((self.size * self.size), dtype="float32")
        for a, p in visits.items():
            if a is None:
                continue
            y, x = a.dest
            policies[y * self.size + x] = p
        return (policies,)
