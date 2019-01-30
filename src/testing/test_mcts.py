from testing import assertion
from controller.mcts import MCTS, Node
from controller.latrunculi import Latrunculi

def run_tests():
    # Test selection.
    # Test first selection.
    game = Latrunculi(8)
    mcts = MCTS(game)
    state = game.start_state()

    actions = game.actions(state)
    root = Node(state, [])
    child_nodes = [Node(game.result(state, action), [], root) for action in actions]
    root.children = child_nodes
    node = mcts.select(root, 0)

    assertion.assert_equal(child_nodes[0], node, "first selection")

    # =================================
    # Test exploitation of promising node.
    root.visits = 2
    for child in child_nodes:
        child.wins = 2
        child.visits = 2

    child_nodes[4].wins = 3
    node = mcts.select(root, 0)

    assertion.assert_equal(child_nodes[4], node, "exploitation selection")

    # =================================
    # Test exploration of less visited node.
    root.visits = 3
    for child in child_nodes:
        child.wins = 4
        child.visits = 3

    child_nodes[3].wins = 3
    child_nodes[3].visits = 2
    node = mcts.select(root, 0)

    assertion.assert_equal(child_nodes[3], node, "exploration selection")

    # =================================
    # Test expansion.
    # Test correct number of children.
    root = Node(state, [])
    mcts.expand(root, actions)

    assertion.assert_equal(16, len(root.children), "expansion correct num of children")

    # =================================
    # Test correct parent
    parent_is_root = True
    for child in root.children:
        parent_is_root = child.parent == root and parent_is_root

    assertion.assert_true(parent_is_root, "expansion correct parent")

    # =================================
    # Test simulation/rollout
