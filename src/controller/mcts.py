"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
from math import inf
from time import time
from controller.game_ai import GameAI
from view.log import log
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

    def __str__(self):
        children = ", ".join([str(c) for c in self.children])
        return ("[Node: turn={}, visits={}, wins={},\nchildren=\n    [{}]]").format(
            self.state.player, self.visits, self.wins, children.replace("\n", "\n    "))

class MCTS(GameAI):
    """
    Implementation of MCTS. This is implemented in terms
    of the four stages of the algorithm: Selection, Expansion,
    Simulation and Backpropagation.
    """
    state_map = dict()

    EXPLORE_PARAM = 2 # Used when choosing which node to explore or exploit.
    ITERATIONS = 5 # Number of times to run MCTS, per action taken in game.

    def select(self, node, sim_acc):
        """
        Select a node to run simulations from.
        Nodes are chosen according to how they maximize
        the UCB1 formula = w(i) + c * sqrt (ln N(i) / n(i))).
        Where
            - w(i) = wins of current node.
            - n(i) = times current node was visited.
            - c = exploration constant, 2 usually.
            - N(i) = accummulated visits of all parents of current node.
        This assures a balance between exploring new nodes,
        and exploiting nodes that are known to result in good outcomes.
        """
        if node.children == []: # Node is a leaf.
            return node

        sim_acc += node.visits
        best_node = node.children[0] # Choose first node if all are equal.
        best_value = 0
        for child in node.children:
            if child.visits == 0:
                # Node has not been visited. It is chosen immediately.
                best_node = child
                break
            else:
                # UCB1 formula (split up, for readability).
                exploit = child.wins + self.EXPLORE_PARAM
                val = exploit * np.sqrt(np.log(sim_acc) / child.visits)
                if val > best_value:
                    best_value = val
                    best_node = child

        return self.select(best_node, sim_acc)

    def expand(self, node, actions):
        """
        Expand the tree with new nodes, corresponding to
        taking any possible actions from the current node.
        """
        children = [Node(self.game.result(node.state, action), [], node) for action in actions]
        node.children = children

    def simulate(self, state, actions):
        """
        Simulate a random action from the given state and the given
        possible actions. Return the result of the random action.
        """
        chosen_action = actions[int(np.random.uniform(0, len(actions)))] # Chose random action.
        return self.game.result(state, chosen_action)

    def back_propogate(self, node, value):
        """
        After a full simulation, propogate result up the tree.
        """
        node.visits += 1
        node.wins += value
        if node.parent is None:
            return
        self.back_propogate(node.parent, value)

    def rollout(self, og_state, node):
        """
        Make random simulations until a terminal state
        is reached. Then the utility value of this state,
        for the current player, is returned.
        """
        state = node.state
        counter = 0

        while not self.game.terminal_test(state):
            actions = self.game.actions(state)
            state = self.simulate(state, actions)
            counter += 1
        
        log("Iterations spent on rollout: {}".format(counter))
        return self.game.utility(state, og_state.player)

    def execute_action(self, state):
        super.__doc__
        time_total_b = time()
        # Get state ID and look the corresponding node up in the state map.
        state_id = state.stringify()
        original_node = None
        try:
            # Node exists, we have run MCTS on this state before.
            original_node = self.state_map[state_id]
            log("State has been visited before")
        except KeyError:
            # Node does not exist, we create a new one, and add it to our state map.
            log("State has NOT been visited before")
            actions = self.game.actions(state)
            original_node = Node(state, [])
            self.expand(original_node, actions)
            self.state_map[state_id] = original_node

        # Perform iterations of selection, simulation, expansion, and back propogation.
        # After the iterations are done, the child of the original node with the highest
        # number of wins are chosen as the best action.
        for _ in range(self.ITERATIONS):
            node = self.select(original_node, 0)
            if node.visits > 0:
                # Expand tree from available actions. Select first expanded node as
                # new current and simulate an action from this nodes possible actions.
                actions = self.game.actions(node.state)
                self.expand(node, actions)
                node = node.children[0] # Select first child of expanded Node.
                node.state.player = not node.state.player

            # Perform rollout, simulate till end of game and return outcome.
            value = self.rollout(node.state, node)
            self.back_propogate(node, value)

            node = original_node

        best_node = max(original_node.children, key=lambda n: n.wins)
        log("Total action duration: {} s".format(time() - time_total_b))
        return best_node.state

    def __str__(self):
        states_explored = ""
        for v in self.state_map:
            states_explored += str(self.state_map[v]) + ",\n"
        return "[MCTS:\n{}]".format(states_explored)
