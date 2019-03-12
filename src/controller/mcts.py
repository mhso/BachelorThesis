"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
import numpy as np
import constants
from controller.game_ai import GameAI
from view.log import log

class Node():
    action = None
    state = None
    visits = 0
    value = 0
    mean_value = 0

    def __init__(self, state, action, prior_prob=0, parent=None):
        self.state = state
        self.action = action
        self.parent = parent
        self.prior_prob = prior_prob
        self.children = {}

    def pretty_desc(self):
        return "Node: a: {}, n: {}, v: {}, m: {}, p: {}".format(
            self.action, self.visits, self.value, "%.3f" % self.mean_value, "%.3f" % self.prior_prob)

    def __str__(self):
        return self.pretty_desc()

    def crazy_print(self):
        children = ", ".join([str(c) for c in self.children.values()])
        return ("[Node: turn={}, visits={}, value={},\nchildren=\n    [{}]]").format(
            self.state.player, self.visits, self.value, children.replace("\n", "\n    "))

class MCTS(GameAI):
    """
    Implementation of MCTS. This is implemented in terms
    of the four stages of the algorithm: Selection, Expansion,
    Simulation and Backpropagation.
    """
    state_map = dict()
    connection = None

    EXPLORE_PARAM = 2 # Used when choosing which node to explore or exploit.
    ITERATIONS = 800 # Number of times to run MCTS, per action taken in game.
    MAX_MOVES = 5000 # Max moves before a simulation is deemed a draw.

    def __init__(self, game, playouts=None):
        super().__init__(game)
        if playouts:
            self.ITERATIONS = playouts
        else:
            self.ITERATIONS = constants.MCTS_ITERATIONS

        log("MCTS is using {} playouts and {} max moves.".format(self.ITERATIONS, self.MAX_MOVES))

    def ucb_score(self, node, parent_visits):
        # PUCT formula.
        #e_base = constants.EXPLORE_BASE
        #e_init = constants.EXPLORE_INIT
        #explore_val = np.log((1 + child.visits + e_base) / e_base) + e_init
        explore_val = 1.27 # TODO: Maybe change later.
        val = node.mean_value + (
            explore_val * node.prior_prob
            * parent_visits / (1+node.visits)
        )
        return val

    def select(self, node):
        """
        Select a node to run simulations from.
        Nodes are chosen according to how they maximize
        the PUCT formula = Q(i) + c * P(i) * sqrt (N(i) / (1 + n(i))
        Where
            - Q(i) = mean value of node (node value / node visits).
            - c = exploration rate.
            - P(i) = prior probability of selecting action in node (i).
            - N(i) = visits of parent node.
            - n(i) = times current node was visited.
        This assures a balance between exploring new nodes,
        and exploiting nodes that are known to result in good outcomes.
        """
        if node.children == {}: # Node is a leaf.
            return node
        parent_sqrt = np.sqrt(node.visits)
        best_node = max(node.children.values(), key=lambda n: self.ucb_score(n, parent_sqrt))

        return self.select(best_node)

    def expand(self, node, actions):
        """
        Expand the tree with new nodes, corresponding to
        taking any possible actions from the current node.
        """
        node_probability = 1/len(actions) # Probability of selecting node.
        node.children = {action: Node(self.game.result(node.state, action), action, node_probability, node) for action in actions}

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

    def evaluate(self, node):
        """
        Use the neural network to obtain a prediction of the
        outcome of the game, as well as probability distribution
        of available actions, from the current state.
        """
        state = node.state
        actions = self.game.actions(state)
        # Get network evaluation from main process.
        self.connection.send(("evaluate", self.game.structure_data(state)))
        policy_logits, value = self.connection.recv()

        logit_map = self.game.map_logits(actions, policy_logits)
        policy_sum = sum(logit_map.values())

        # Expand node.
        for a, p in logit_map.items():
            node.children[a] = Node(self.game.result(state, a), a, p / policy_sum if policy_sum else 0, node)

        return value

    def choose_action(self, node):
        child_nodes = [n for n in node.children.values()]
        visit_counts = [n.visits for n in child_nodes]

        if len(self.game.history) < constants.NUM_SAMPLING_MOVES:
            # Perform softmax random selection of available actions,
            # based on visit counts.
            sum_visits = sum(visit_counts)
            return np.random.choice(child_nodes,
                                    p=[v/sum_visits for v in visit_counts])
        # Return node with highest visit count.
        return max(child_nodes, key=lambda n: n.visits)

    def add_exploration_noise(self, node):
        """
        Add noise to prior value of node, to encourage
        exploration of new nodes. Not currently used.
        """
        actions = node.children.keys()
        noise = np.random.gamma(constants.NOISE_BASE, 1, len(actions))
        frac = constants.NOISE_FRACTION
        for a, n in zip(actions, noise):
            node.children[a].prior_prob *= (1 - frac) + n * frac

    def execute_action(self, state):
        super.__doc__
        log("MCTS is calculating the best move...")

        root_node = Node(state, None)
        self.evaluate(root_node)

        # Perform iterations of selection, simulation, expansion, and back propogation.
        # After the iterations are done, the child of the original node with the highest
        # number of mean value (value/visits) are chosen as the best action.
        for i in range(self.ITERATIONS):
            node = self.select(root_node)

            # Perform rollout, simulate till end of game and return outcome.
            value = self.evaluate(node)
            self.back_propagate(node, -value if node.state.player == root_node.state.player else value)

            node = root_node

        for node in root_node.children.values():
            log(node.pretty_desc())

        best_node = self.choose_action(root_node)

        log("MCTS action: {}, likelihood of win: {}%".format(best_node.action, int((best_node.mean_value*50)+50)))
        self.game.store_search_statistics(root_node)
        return best_node.state

    def __str__(self):
        states_explored = ""
        for v in self.state_map:
            states_explored += str(self.state_map[v]) + ",\n"
        return "[MCTS:\n{}]".format(states_explored)
