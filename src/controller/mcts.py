"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
from math import inf
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
    To do:
    - Make method for matching action with a state.
    - Model the tree structure.
    - Expansion adds all possible moves, simulation choosen one.
    - Handle teams.
    """
    current = None
    EXPLORE_PARAM = 1.42 # Used when choosing which node to explore or exploit.

    def find(self, node, state):
        if node.state == state:
            return node
        return None

    def choose(self, node, sim_acc):
        if node.children == []:
            return node
        sim_acc += node.visits
        best_node = None
        best_value = 0
        for child in node.children:
            if node.visits == 0:
                # Node has not been visited. It's value is set to infinity.
                val = inf
            else:
                eq1 = node.wins / node.visits
                eq2 = eq1 + self.EXPLORE_PARAM
                val = eq2 * np.sqrt(np.log(sim_acc)) / node.visits

            if val > best_value:
                best_value = val
                best_node = child

        self.choose(best_node, sim_acc)

    def select(self, state):
        if self.current is None:
            self.current = Node(state, [])

        node = self.current

        actions = self.game.actions(node.state)
        next_node = self.choose(node, 0)

        if next_node.visits == 0:
            # Do not expand tree. Do not update current node.
            return self.simulate(next_node.state, actions)

        # Expand tree from available actions. Select first expanded node
        # as new current and simulate an action from this node's possible actions.
        self.expand(node, actions)
        self.current = node.children[0]
        new_actions = self.game.actions(self.current.state)

        return self.simulate(self.current.state, new_actions)

    def expand(self, node, actions):
        children = [Node(action, [], node) for action in actions]
        node.children = children

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
