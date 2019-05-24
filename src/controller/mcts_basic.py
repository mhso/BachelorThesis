"""
------------------------------------
mcts: Monte Carlo Tree Search.
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
    probability = 0

    def __init__(self, state, action, probability=1, parent=None):
        self.state = state
        self.action = action
        self.parent = parent
        self.probability = probability

    def pretty_desc(self):
        return "Node: a: {}, n: {}, v: {}, m: {}, p: {}".format(
            self.action, self.visits, self.value, "%.3f" % self.mean_value, "%.3f" % self.probability)

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
    state_map = dict()

    EXPLORE_PARAM = 2 # Used when choosing which node to explore or exploit.
    ITERATIONS = 100 # Number of times to run MCTS, per action taken in game.

    def __init__(self, game, playouts=None):
        super().__init__(game)
        if playouts is not None:
            self.ITERATIONS = Config.MCTS_BASIC_ITERATIONS
            self.MAX_MOVES = 1000

        log("MCTS is using {} playouts and {} max moves.".format(self.ITERATIONS, self.MAX_MOVES))

    def set_config(self, config):
        GameAI.set_config(self, config)
        self.ITERATIONS = config.MCTS_BASIC_ITERATIONS

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
        if node.children == {}: # Node is a leaf.
            return node

        sim_acc += node.visits
        acc_sqrt = np.sqrt(sim_acc)
        best_node = None
        best_value = -1
        for child in node.children.values():
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
        original_node = Node(state, None)
        """
        state_id = state.stringify()
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
        """

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
                node = node.children[actions[0]] # Select first child of expanded Node.
            #self.state_map[node.state.stringify()] = node

            # Perform rollout, simulate till end of game and return outcome.
            value = self.rollout(original_node.state, node)
            #print(f"OG is: {original_node.state.player}, we are: {node.state.player}, value is: {value}")
            self.back_propagate(node, -value if node.state.player == original_node.state.player else value)

            node = original_node

        for node in original_node.children.values():
            log(node.pretty_desc())

        best_node = max(original_node.children.values(), key=lambda n: n.visits)
        original_node = None

        #Graph.plot_data("Player {}".format(state.str_player()), None, best_node.mean_value, "Turn", "Win Probability")
        log("MCTS action: {}, likelihood of win: {}%".format(best_node.action, int((best_node.mean_value*50)+50)))

        return best_node.state
