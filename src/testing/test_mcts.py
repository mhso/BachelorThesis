from time import time
from testing import assertion
from controller.mcts import MCTS, Node
from controller.latrunculi import Latrunculi
from controller.latrunculi_pl import Latrunculi_pl

def run_tests():
    # Test selection.
    # Test first selection.
    game = Latrunculi_pl(8)
    mcts = MCTS(game)
    state = game.start_state()

    actions = game.actions(state)
    root = Node(state, None, [])
    probability = 1/len(actions)
    child_nodes = [Node(game.result(state, action), action, [], probability, root) for action in actions]
    root.children = child_nodes
    node = mcts.select(root, 0)

    assertion.assert_equal(child_nodes[0], node, "first selection")

    # =================================
    # Test exploitation of promising node.
    root.visits = 3
    for child in child_nodes:
        child.value = 2
        child.visits = 3

    child_nodes[4].value = 3
    node = mcts.select(root, 0)

    assertion.assert_equal(child_nodes[4], node, "exploitation selection")

    # =================================
    # Test exploration of less visited node.
    root.visits = 3
    for child in child_nodes:
        child.value = 4
        child.visits = 3

    child_nodes[3].value = 3
    child_nodes[3].visits = 2
    node = mcts.select(root, 0)

    assertion.assert_equal(child_nodes[3], node, "exploration selection")

    # =================================
    # Test expansion.
    # Test correct number of children.
    root = Node(state, None, [])
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

def run_iteration_tests(log_type=None):
    print("run iteration timing test MCTS")
    game = Latrunculi(4, 55)
    state = game.start_state()

    time_b = time()

    mcts = MCTS(game, 100)
    mcts.execute_action(state)

    time_taken = time() - time_b
    print("Time taken to execute MCTS move: {} s".format(time_taken))
    """
    if log_type == 'excel':
        # Appending results to standard excel file "test_results.xlsx"
        row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "Latrunculi", counter, (time() - time_b))
        ExcelUtil.excel_append_row(row)
    elif log_type == 'sql':
        row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "Latrunculi", counter, (time() - time_b))
        sql_conn = SqlUtil.connect()
        SqlUtil.test_iteration_timing_insert_row(sql_conn, row)
    """
    return time_taken


