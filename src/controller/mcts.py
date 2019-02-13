"""
------------------------------------
mcts: Monte Carlo Tree Search.
------------------------------------
"""
import numpy as np
from controller.game_ai import GameAI
from view.log import log
from view.graph import Graph

class Node():
    action = None
    state = None
    children = None
    parent = None
    visits = 0
    value = 0
    mean_value = 0
    probability = 0

    def __init__(self, state, action, children, probability=1, parent=None):
        self.state = state
        self.action = action
        self.children = children
        self.probability = probability
        self.parent = parent

    def pretty_desc(self):
        return "Node: a: {}, n: {}, v: {}, m: {}, p: {}".format(
            self.action, self.visits, self.value, "%.3f" % self.mean_value, "%.3f" % self.probability)

    def __str__(self):
        children = ", ".join([str(c) for c in self.children])
        return ("[Node: turn={}, visits={}, value={},\nchildren=\n    [{}]]").format(
            self.state.player, self.visits, self.value, children.replace("\n", "\n    "))

class MCTS(GameAI):
    """
    Implementation of MCTS. This is implemented in terms
    of the four stages of the algorithm: Selection, Expansion,
    Simulation and Backpropagation.
    """
    state_map = dict()

    EXPLORE_PARAM = 2 # Used when choosing which node to explore or exploit.
    ITERATIONS = 100 # Number of times to run MCTS, per action taken in game.
    MAX_MOVES = 5000 # Max moves before a simulation is deemed a draw.

    def __init__(self, game, playouts=None):
        super().__init__(game)
        if self.game.size > 3:
            playout_options = [1000, 100, 35, 20, 10, 5, 5]
            max_moves = [400, 1200, 1600, 2400, 5000, 5000, 5000]
            self.ITERATIONS = playout_options[self.game.size-4]
            self.MAX_MOVES = max_moves[self.game.size-4]
        if playouts is not None:
            self.ITERATIONS = playouts

        print("MCTS is using {} playouts and {} max moves.".format(self.ITERATIONS, self.MAX_MOVES))

    def select(self, node, sim_acc):
        """
        Select a node to run simulations from.
        Nodes are chosen according to how they maximize
        the PUCT formula = Q(i) + c * P(i) * sqrt (N(i) / (1 + n(i))
        Where
            - Q(i) = mean value of node (node value / node visits).
            - c = exploration constant, 2 usually.
            - P(i) = probability of selecting action in node (i).
            - N(i) = accummulated visits of all parents of current node.
            - n(i) = times current node was visited.
        This assures a balance between exploring new nodes,
        and exploiting nodes, that are known to result in good outcomes.
        """
        if node.children == []: # Node is a leaf.
            return node

        sim_acc += node.visits
        acc_sqrt = np.sqrt(sim_acc)
        best_node = node.children[0] # Choose first node if all are equal.
        best_value = 0
        for child in node.children:
            if child.visits == 0:
                # Node has not been visited. It is chosen immediately.
                best_node = child
                break
            else:
                # PUCT formula.
                val = child.mean_value + (
                    self.EXPLORE_PARAM * child.probability
                    * acc_sqrt / (1+child.visits)
                )

                if val > best_value:
                    best_value = val
                    best_node = child

        return self.select(best_node, sim_acc)

    def expand(self, node, actions):
        """
        Expand the tree with new nodes, corresponding to
        taking any possible actions from the current node.
        """
        node_probability = 1/len(actions) # Probability of selecting node.
        children = [Node(self.game.result(node.state, action), action, [], node_probability, node) for action in actions]
        node.children = children

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
        self.back_propagate(node.parent, 1-value)

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
            #if counter % 25 == 0:
                #print("MOVE {}, BOARD: {}".format(counter, state.board))
                #print("MOVE {}, PIECES: {}".format(counter, state.pieces))
            counter += 1

        #log("Iterations spent on rollout: {}".format(counter))
        return self.game.utility(state, og_state.player)

    def execute_action(self, state):
        super.__doc__
        log("MCTS is calculating the best move...")

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
            original_node = Node(state, None, [])
            self.expand(original_node, actions)
            self.state_map[state_id] = original_node

        # Perform iterations of selection, simulation, expansion, and back propogation.
        # After the iterations are done, the child of the original node with the highest
        # number of mean value (value/visits) are chosen as the best action.
        for _ in range(self.ITERATIONS):
            node = self.select(original_node, 0)
            if node.visits > 0 and not self.game.terminal_test(node.state):
                # Expand tree from available actions. Select first expanded node as
                # new current and simulate an action from this nodes possible actions.
                actions = self.game.actions(node.state)
                self.expand(node, actions)
                node = node.children[0] # Select first child of expanded Node.
            self.state_map[node.state.stringify()] = node

            # Perform rollout, simulate till end of game and return outcome.
            value = self.rollout(original_node.state, node)
            self.back_propagate(node, 1-value if node.state.player == original_node.state.player else value)

            node = original_node

        for node in original_node.children:
            log(node.pretty_desc())

        best_node = max(original_node.children, key=lambda n: n.mean_value)

        #Graph.plot_data("Player {}".format(state.str_player()), None, best_node.mean_value, "Turn", "Win Probability")
        log("MCTS action: {}, confidence of win: {}%".format(best_node.action, int(best_node.mean_value*100)))

        return best_node.state

    def __str__(self):
        states_explored = ""
        for v in self.state_map:
            states_explored += str(self.state_map[v]) + ",\n"
        return "[MCTS:\n{}]".format(states_explored)
