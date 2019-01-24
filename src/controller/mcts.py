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
    """
    current = None
    EXPLORE_PARAM = 1.42 # Used when choosing which node to explore or exploit.

    def choose(self, node, sim_acc):
        """
        Choose a node to run simulations from.
        Nodes are chosen according to the node which maximizes
        the UCB1 formula = w(i) / n(i) + c * sqrt (ln N(i) / n(i))).
        Where
            - w(i) = wins of current node.
            - n(i) = times current node was visited.
            - c = exploration constant, ~2.
            - N(i) = accummulated visits of all parents.
        This assures a balance between exploring
        new nodes, and exploiting nodes that are known to be good moves.
        """
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
                # UCB1 formula (split up, for readability).
                p1 = node.wins / node.visits
                p2 = p1 + self.EXPLORE_PARAM
                val = p2 * np.sqrt(np.log(sim_acc)) / node.visits

            if val > best_value:
                best_value = val
                best_node = child

        self.choose(best_node, sim_acc)

    def select(self, state):
        """
        Select the node, for which to run simulation from.
        """
        if self.current is None:
            self.current = Node(state, [])

        next_node = self.choose(self.current, 0)

        return next_node

    def expand(self, node, actions):
        """
        Expand the tree with new nodes, corresponding to
        taking any possible actions from the current node.
        """
        children = [Node(action, [], node) for action in actions]
        node.children = children

    def simulate(self, state, actions):
        """
        Simulate a random action from the given state and the given
        possible actions. Return the result of the random action.
        """
        chosen_action = actions[int(np.random.uniform(0, len(actions)))] # Chose random action.
        return self.game.result(state, chosen_action)

    def back_propogate(self, node):
        node.visited += 1
        if node.parent is None:
            return
        self.back_propogate(node.parent)

    def execute_action(self, state):
        super.__doc__
        next_node = self.select(state)
        curr = self.current
        actions = self.game.actions(curr.state)

        if next_node.visits == 0:
            # Do not expand tree. Do not update current node.
            return self.simulate(next_node.state, actions)

        # Expand tree from available actions. Select first expanded node
        # as new current and simulate an action from this node's possible actions.
        self.expand(curr, actions)
        self.current = curr.children[0]
        new_actions = self.game.actions(self.current.state)

        return self.simulate(self.current.state, new_actions)
