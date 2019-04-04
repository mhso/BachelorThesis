"""
-----------------------------
connect_four: We all know it.
-----------------------------
"""
from controller.game import Game
from model.state import State, Action
from scipy.signal import convolve2d
import numpy as np

class Connect_Four(Game):
    __observers = []

    def __init__(self, size, rand_seed=None):
        Game.__init__(self)
        self.size = size
        self.terminal_kernels = [
            np.array([[1, 1, 1, 1]]),
            np.array([[1], [1], [1], [1]]),
            np.eye(4, 4),
            np.fliplr(np.eye(4, 4))
        ]
        self.num_actions = self.size * self.size

    def start_state(self):
        super.__doc__
        return State(np.zeros((self.size, self.size), dtype='b'), True)

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        board = state.board
        action_list = []
        for x in range(0, self.size):
            for y in range(self.size-1, -1, -1):
                if board[y][x] == 0:
                    action_list.append(Action(None, (y, x)))
                    break
        return action_list

    def result(self, state, action):
        super.__doc__
        y, x = action.dest
        copy_arr = np.copy(state.board)
        copy_arr[y][x] = 1 if state.player else -1
        return State(copy_arr, not state.player)

    def terminal_test(self, state):
        super.__doc__
        if (state.board == 0).sum() == 0:
            return True
        for kernel in self.terminal_kernels:
            conv = convolve2d(state.board, kernel, mode="valid")
            if (conv == 4).sum() > 0 or (conv == -4).sum() > 0:
                return True
        return False

    def utility(self, state, player):
        super.__doc__
        for kernel in self.terminal_kernels:
            conv = convolve2d(state.board, kernel, mode="valid")
            if (conv == 4).sum() > 0:
                return 1 if player else -1
            elif (conv == -4).sum() > 0:
                return -1 if player else 1
        return 0

    def clone(self):
        clone = Connect_Four(self.size)
        clone.history = self.history
        clone.visit_counts = self.visit_counts
        clone.q_value_history = self.q_value_history
        return clone

    def structure_data(self, state):
        super.__doc__
        pos_pieces = np.where(state.board == 1, state.board, np.zeros((self.size, self.size), dtype='b'))
        neg_pieces = -np.where(state.board == -1, state.board, np.zeros((self.size, self.size), dtype='b'))

        # Structure data as a 4x4x2 stack.
        if state.player:
            return np.array([pos_pieces, neg_pieces])
        else:
            return np.array([neg_pieces, pos_pieces])

    def map_logits(self, actions, logits):
        action_map = dict()
        policy_sum = 0
        for action in actions:
            y, x = action.dest
            logit = np.exp(logits[y * self.size + x % self.size])
            action_map[action] = logit
            policy_sum += logit
        for action, policy in action_map.items():
            action_map[action] = policy/policy_sum if policy_sum else 0
        return action_map

    def map_actions(self, target_policies):
        policies = np.zeros((self.size * self.size))
        for a, p in target_policies.items():
            y, x = a.dest
            policies[y * self.size + x % self.size] = p
        return (policies,)
