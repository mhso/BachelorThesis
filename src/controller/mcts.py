"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
from controller.game_ai import GameAI
import numpy as np

class Node():
    state = None
    children = None
    parent = None
    visits = 0
    wins = 0

    def __init__(self, state, children, parent=None):
        self.state = state
        self.children = children
        self.parent = parent

class MCTS(GameAI):
    """
    Implementation of MCTS. This is implemented in terms
    of the four stages of the algorithm: Selection, Expansion,
    Simulation and Backpropagation.
    """
    root = None
    EXPLORE_PARAM = 1.42 # Used when choosing which node to explore or exploit.

    def find(self, node, state):
        if node.state == state:
            return node
        return None

    def choose(self, node, sim_acc):
        sim_acc += node.visits
        if not np.size(node.children):
            return node.state
        best_node = None
        best_value = 0
        for child in node.children:
            eq1 = node.wins / node.visits
            eq2 = eq1 + self.EXPLORE_PARAM
            val = eq2 * np.sqrt(np.log(sim_acc)) / node.visits
            if val > best_value:
                best_value = val
                best_node = child

        self.choose(best_node, sim_acc)

    def select(self, state):
        leaf = state
        if self.root is not None:
            curr_node = np.extract(lambda node: node.state == state, self.root)[0]

            leaf = self.choose(curr_node, 0)
            leaf_state = leaf.state

        actions = self.game.actions(leaf_state)
        new_state = self.simulate(leaf, actions)
        self.expand(new_state)

        return new_state

    def expand(self, new_state):
        node = Node(new_state, np.array([]))
        np.append(self.root, node)

    def simulate(self, state, actions):
        chosen_action = actions[int(np.random.uniform(0, len(actions)))] # Chose random action.
        return self.game.result(state, chosen_action)

    def back_propogate(self, node):
        node.visited += 1
        if node.parent is None:
            return
        self.back_propogate(node.parent)

    def execute_action(self, state):
        super.__doc__
        return self.select(state)
