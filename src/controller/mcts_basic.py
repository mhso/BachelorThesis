"""
------------------------------------
mcts_basic: Monte Carlo Tree Search.
------------------------------------
"""
import numpy as np
from controller.game_ai import GameAI
from config import Config
from view.log import log
from view.graph import Graph

class Node():
    action = None
    state = None
    children = {}
    visits = 0
    value = 0
    mean_value = 0

    def __init__(self, state, action, parent=None):
        self.state = state
        self.action = action
        self.parent = parent

    def pretty_desc(self):
        return "Node: a: {}, n: {}, v: {}, m: {}".format(
            self.action, self.visits, self.value, "%.3f" % self.mean_value)

    def __str__(self):
        children = ", ".join([str(c) for c in self.children.values()])
        return ("[Node: turn={}, visits={}, value={},\nchildren=\n    [{}]]").format(
            self.state.player, self.visits, self.value, children.replace("\n", "\n    "))

class MCTS_Basic(GameAI):
    """
    Implementation of MCTS. This is implemented in terms
    of the four stages of the algorithm: Selection, Expansion,
    Simulation and Backpropagation.
    """
    EXPLORE_PARAM = 2 # Used when choosing which node to explore or exploit.
    ITERATIONS = 100 # Number of times to run MCTS, per action taken in game.

    def __init__(self, game, playouts=Config.MCTS_ITERATIONS):
        super().__init__(game)
        if playouts is not None:
            self.ITERATIONS = playouts
            self.MAX_MOVES = 5000
        elif self.game.size > 3:
            playout_options = [800, 200, 35, 20, 10, 5, 5]
            max_moves = [400, 1200, 1600, 2400, 5000, 5000, 5000]
            self.ITERATIONS = playout_options[self.game.size-4]
            self.MAX_MOVES = max_moves[self.game.size-4]

        log("MCTS is using {} playouts and {} max moves.".format(self.ITERATIONS, self.MAX_MOVES))

    def select(self, node):
        """
        Select a node to run simulations from.
        Nodes are chosen according to how they maximize
        the UCB formula = v(i) + C * sqrt (ln(N(i)) / n(i))
        Where
            - v(i) = mean value of node (node value / node visits).
            - C = exploration constant, 2 usually.
            - N(i) = number of visits of the parent of current node.
            - n(i) = times current node was visited.
        This assures a balance between exploring new nodes,
        and exploiting nodes, that are known to result in good outcomes.
        """
        if node.children == {}: # Node is a leaf.
            return node

        parent_log = np.log(node.visits)
        best_node = None
        best_value = -1
        for child in node.children.values():
            if child.visits == 0:
                # Node has not been visited. It is chosen immediately.
                best_node = child
                break
            else:
                # UCB formula.
                val = child.mean_value + self.EXPLORE_PARAM * (parent_log / child.visits)

                if val > best_value:
                    best_value = val
                    best_node = child

        return self.select(best_node)

    def expand(self, node, actions):
        """
        Expand the tree with new nodes, corresponding to
        taking any possible actions from the current node.
        """
        node.children = {action: Node(self.game.result(node.state, action), action, parent=node) for action in actions}

    def simulate(self, state, actions):
        """
        Simulate a random action from the given state and the given
        possible actions. Return the result of the random action.
        """
        chosen_action = actions[int(np.random.uniform(0, len(actions)))] # Chose random action.
        return self.game.result(state, chosen_action)

    def back_propagate(self, node, value):
        """
        After a full simulation, propagate result up the tree.
        Invert value at every node, to align 'perspective' to
        the current player of that node.
        """
        node.visits += 1
        node.value += value
        node.mean_value = node.value / node.visits

        if node.parent is None:
            return
        self.back_propagate(node.parent, -value)

    def rollout(self, og_state, node):
        """
        Make random simulations until a terminal state
        is reached. Then the utility value of this state,
        for the current player, is returned.
        """
        state = node.state
        counter = 0

        while not self.game.terminal_test(state) and counter < self.MAX_MOVES:
            actions = self.game.actions(state)
            state = self.simulate(state, actions)
            counter += 1

        return self.game.utility(state, og_state.player)

    def execute_action(self, state):
        super.__doc__
        log("MCTS is calculating the best move...")

        root_node = Node(state, None)

        # Perform iterations of selection, simulation, expansion, and back propogation.
        # After the iterations are done, the child of the root node with the highest
        # number of mean value (value/visits) are chosen as the best action.
        for _ in range(self.ITERATIONS):
            node = self.select(root_node)
            if node.visits > 0 and not self.game.terminal_test(node.state):
                # Expand tree from available actions. Select first expanded node as
                # new current and simulate an action from this nodes possible actions.
                actions = self.game.actions(node.state)
                self.expand(node, actions)
                node = node.children[actions[0]] # Select first child of expanded Node.

            # Perform rollout, simulate till end of game and return outcome.
            value = self.rollout(root_node.state, node)
            self.back_propagate(node, -value if node.state.player == root_node.state.player else value)

            node = root_node

        for node in root_node.children.values():
            log(node.pretty_desc())

        best_node = max(root_node.children.values(), key=lambda n: n.visits)
        root_node = None

        log("MCTS action: {}, likelihood of win: {}%".format(best_node.action, int((best_node.mean_value*50)+50)))

        return best_node.state
