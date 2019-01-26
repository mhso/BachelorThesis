from testing import assertion
from controller.mcts import MCTS, Node
from controller.latrunculi import Latrunculi

def run_tests():
    print("-=-=-=- MCTS TESTS -=-=-=-")
    # Test selection.
    # Test number of child nodes.
    game = Latrunculi(8)
    mcts = MCTS(game)
    state = game.start_state()
    num_actions = 16

    root = Node(state, [])
    node = mcts.select(root, 0)

    assertion.assert_equal(num_actions, len(root.children), "selection first action")

    # =================================
