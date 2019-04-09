"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
import numpy as np
from config import Config
from controller.game_ai import GameAI
from view.log import log

class Node():
    def __init__(self, state, action, prior_prob=0, parent=None):
        self.state = state
        self.action = action
        self.parent = parent
        self.prior_prob = prior_prob
        self.children = {}
        self.visits = 0
        self.value = 0
        self.q_value = 0

    def pretty_desc(self):
        return "Node: a: {}, n: {}, v: {}, m: {}, p: {}".format(
            self.action, self.visits, self.value, "%.3f" % self.q_value, "%.3f" % self.prior_prob)

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
    cfg = None
    chosen_node = None

    def __init__(self, game, playouts=None):
        super().__init__(game)
        if playouts:
            self.ITERATIONS = playouts
        else:
            self.ITERATIONS = Config.MCTS_ITERATIONS

        log("MCTS is using {} playouts.".format(self.ITERATIONS))

    def set_config(self, config):
        self.cfg = config
        self.ITERATIONS = config.MCTS_ITERATIONS

    def ucb_score(self, node, parent_visits):
        """
        PUCT (Polynomial Upper Confident for Trees) formula.
        Q(s, a) + C(s) * P(s, a) * sqrt(N(s)) / (1 + N(s, a)),
        where
            - Q(s, a) = q-value of node. Visits/value.
            - N(s) = parent visit count of current node.
            - C(s) = exploration rate. Scales according to simulations in AZ.
                     We keep it as a constant for simplicity.
            - P(s, a) = prior probability of selecting action in node.
            - N(s, a) = visits of current node.
        """
        #e_base = self.cfg.EXPLORE_BASE
        #e_init = self.cfg.EXPLORE_INIT
        #explore_val = np.log((1 + child.visits + e_base) / e_base) + e_init
        explore_val = 1.27 # TODO: Maybe change later.
        val = node.q_value + (
            explore_val * node.prior_prob
            * parent_visits / (1+node.visits)
        )
        return val

    def select(self, node):
        """
        Select a node to run simulations from.
        Nodes are recursively chosen according to how they maximize
        the PUCT formula, until a leaf is reached.
        """
        if node.children == {}: # Node is a leaf.
            return node
        parent_sqrt = np.sqrt(node.visits)
        best_node = max(node.children.values(), key=lambda n: self.ucb_score(n, parent_sqrt))

        return self.select(best_node)

    def expand(self, node, actions, policies):
        """
        Expand the tree with new nodes, corresponding to
        taking any possible actions from the current node.
        """
        logit_map = self.game.map_logits(actions, policies)
        policy_sum = sum(logit_map.values())
        for a, p in logit_map.items():
            node.children[a] = Node(self.game.result(node.state, a), a, p / policy_sum if policy_sum else 0, node)

    def back_propagate(self, node, value):
        """
        After a full simulation, propagate result up the tree.
        Invert value at every node, to align 'perspective' to
        the current player of that node.
        """
        node.visits += 1
        node.value += value
        node.q_value = node.value / node.visits

        if node.parent is None:
            return
        self.back_propagate(node.parent, -value)

    def set_evaluation_data(self, node, policy_logits, value):
        """
        Use the neural network to obtain a prediction of the
        outcome of the game, as well as probability distribution
        of available actions from the current state.
        """
        state = node.state
        actions = self.game.actions(state)
        new_value = value
        if self.game.terminal_test(state):
            new_value = self.game.utility(state, state.player)

        if actions == [None]: # Only action is a 'pass'.
            return new_value

        # Expand node.
        self.expand(node, actions, policy_logits)

        return new_value

    def softmax_sample(self, child_nodes, visit_counts, tempature=0.5):
        """
        Perform softmax sampling on a set of nodes
        based on a probability distribution of their
        visit counts.
        """
        sum_visits = sum(visit_counts)
        prob_visits = [v/sum_visits for v in visit_counts]
        exps = np.exp(prob_visits) * tempature

        return np.random.choice(child_nodes,
                                p=exps/sum(exps))

    def choose_action(self, node):
        """
        When MCTS is finished with it's iterations,
        a final action to take is chosen. If the current
        length of the give is less than a certain threshold,
        softmax sampling is used to select an action, based on
        a probabiliy of visits to that node during MCTS simulation.
        Otherwise, the node with most visits is chosen.
        """
        child_nodes = [n for n in node.children.values()]
        visit_counts = [n.visits for n in child_nodes]
        if len(self.game.history) < self.cfg.NUM_SAMPLING_MOVES:
            # Perform softmax sampling of available actions,
            # based on visit counts.
            return self.softmax_sample(child_nodes, visit_counts)
        # Return node with highest visit count.
        return max(child_nodes, key=lambda n: n.visits)

    def add_exploration_noise(self, node):
        """
        Add Dirichlet noise to prior value of node,
        to encourage exploration of new nodes.
        """
        actions = node.children.keys()
        noise = np.random.gamma(self.cfg.NOISE_BASE, 1, len(actions))
        frac = self.cfg.NOISE_FRACTION
        for a, n in zip(actions, noise):
            node.children[a].prior_prob *= (1 - frac) + n * frac

    def create_root_node(self, state):
        root_node = Node(state, None)
        self.chosen_node = root_node
        return root_node

    def prepare_action(self, root_node):
        if root_node.children == {}: # State has no actions (children).
            self.game.store_search_statistics(None)
            return False # Simulate pass.

        self.add_exploration_noise(root_node)
        return True

    def execute_action(self, node):
        if node.children == {}: # Node is a 'pass' action.
            return self.game.result(node.state, None)
        best_node = self.choose_action(node)
        self.chosen_node = best_node

        log("MCTS action: {}, likelihood of win: {}%".format(best_node.action, int((best_node.q_value*50)+50)))
        self.game.store_search_statistics(node)
        return best_node.state

    def __str__(self):
        states_explored = ""
        for v in self.state_map:
            states_explored += str(self.state_map[v]) + ",\n"
        return "[MCTS:\n{}]".format(states_explored)
