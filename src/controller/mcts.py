"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
import numpy as np
import constants
from controller.game_ai import GameAI
from view.log import log
from view.graph import Graph

class Node():
    action = None
    state = None
    children = {}
    visits = 0
    value = 0
    mean_value = 0

    def __init__(self, state, action, prior_prob=0, parent=None):
        self.state = state
        self.action = action
        self.parent = parent
        self.prior_prob = prior_prob

    def pretty_desc(self):
        return "Node: a: {}, n: {}, v: {}, m: {}, p: {}".format(
            self.action, self.visits, self.value, "%.3f" % self.mean_value, "%.3f" % self.prior_prob)

    def __str__(self):
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
    network = None

    EXPLORE_PARAM = 2 # Used when choosing which node to explore or exploit.
    ITERATIONS = 100 # Number of times to run MCTS, per action taken in game.
    MAX_MOVES = 5000 # Max moves before a simulation is deemed a draw.

    def __init__(self, game, playouts=None):
        super().__init__(game)
        if self.game.size > 3:
            playout_options = [800, 200, 35, 20, 10, 5, 5]
            max_moves = [400, 1200, 1600, 2400, 5000, 5000, 5000]
            self.ITERATIONS = playout_options[self.game.size-4]
            self.MAX_MOVES = max_moves[self.game.size-4]
        if playouts is not None:
            self.ITERATIONS = playouts

        print("MCTS is using {} playouts and {} max moves.".format(self.ITERATIONS, self.MAX_MOVES), flush=True)

    def select(self, node):
        """
        Select a node to run simulations from.
        Nodes are chosen according to how they maximize
        the PUCT formula = Q(i) + c * P(i) * sqrt (N(i) / (1 + n(i))
        Where
            - Q(i) = mean value of node (node value / node visits).
            - c = exploration rate, increases with node visits.
            - P(i) = prior probability of selecting action in node (i).
            - N(i) = visits of parent node.
            - n(i) = times current node was visited.
        This assures a balance between exploring new nodes,
        and exploiting nodes that are known to result in good outcomes.
        """
        if node.children == {}: # Node is a leaf.
            return node

        parent_sqrt = np.sqrt(node)
        best_node = None
        best_value = -1
        for child in node.children.values():
            if child.visits == 0:
                # Node has not been visited. It is chosen immediately.
                best_node = child
                break
            else:
                # PUCT formula.
                e_base = constants.EXPLORE_BASE
                e_init = constants.EXPLORE_INIT
                explore_val = np.log((1 + child.visits + e_base) / e_base) + e_init
                val = child.mean_value + (
                    explore_val * child.prior_prob
                    * parent_sqrt / (1+child.visits)
                )

                if val > best_value:
                    best_value = val
                    best_node = child

        return self.select(best_node)

    def expand(self, node, actions):
        """
        Expand the tree with new nodes, corresponding to
        taking any possible actions from the current node.
        """
        node_probability = 1/len(actions) # Probability of selecting node.
        node.children = {action: Node(self.game.result(node.state, action), action, node_probability, node) for action in actions}

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

    def evaluate(self, node):
        """
        Use the neural network to obtain a prediction of the
        outcome of the game, as well as probability distribution
        of available actions, from the current state.
        """
        state = node.state
        actions = self.game.actions(state)
        # How do we structure policy logits??
        policy_logits, value = self.network.evaluate(self.game.structure_data(state))
        logit_map = self.game.map_logits(actions, policy_logits[0])

        # Expand node.
        policy = {a: np.exp(policy_logits[a]) for a in self.game.actions(state)}
        policy_sum = sum(policy.values())

        for a in policy:
            node.children[a] = Node(self.game.result(state, a), a, policy[a] / policy_sum)

        return value

    def choose_action(self, node):
        child_nodes = node.children.values()
        visit_counts = [n.visits for n in child_nodes]
        if len(self.game.history) < constants.NUM_SAMPLING_MOVES:
            # Perform softmax random selection of available actions,
            # based on visit counts.
            sum_visits = sum(visit_counts)
            return np.random.choice(child_nodes,
                                    p=[visits/sum_visits for visits in visit_counts])
        # Return node with highest visit count.
        return max(child_nodes, key=lambda n: n.mean_value)

    def execute_action(self, state):
        super.__doc__
        log("MCTS is calculating the best move...")

        original_node = Node(state, None)

        # Perform iterations of selection, simulation, expansion, and back propogation.
        # After the iterations are done, the child of the original node with the highest
        # number of mean value (value/visits) are chosen as the best action.
        for _ in range(self.ITERATIONS):
            node = self.select(original_node)

            # Perform rollout, simulate till end of game and return outcome.
            value = self.evaluate(node)
            self.back_propagate(node, -value if node.state.player == original_node.state.player else value)

            node = original_node

        for node in original_node.children.values():
            log(node.pretty_desc())

        best_node = self.choose_action(original_node)

        #Graph.plot_data("Player {}".format(state.str_player()), None, best_node.mean_value, "Turn", "Win Probability")
        log("MCTS action: {}, likelihood of win: {}%".format(best_node.action, int((best_node.mean_value*50)+50)))
        self.game.store_search_statistics(best_node)

        return best_node.state

    def __str__(self):
        states_explored = ""
        for v in self.state_map:
            states_explored += str(self.state_map[v]) + ",\n"
        return "[MCTS:\n{}]".format(states_explored)
