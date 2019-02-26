from threading import Thread
from time import sleep
from testing import assertion
from model.state import Action, State
from model.storage import ReplayStorage
from controller.latrunculi import Latrunculi
from view.graph import Graph

def test_graph(storage):
    sleep(0.5)
    evaluated = False
    if storage.eval_performance():
        evaluated = True
        data = storage.reset_perform_data()
        assertion.assert_true(data != [], "Performance data not empty")
        Graph.plot_data("DATA STUFF", None, data)

    assertion.assert_true(evaluated, "Performance was evaluated")
    assertion.assert_equal([], storage.perform_eval_buffer, "Buffer reset")

def run_tests():
    # Test Action ID.
    action1 = Action((1, 2), (3, 4))
    action2 = Action((0, 0), (3, 4))

    assertion.assert_equal(1234, action1.numeric(), "action numeric id 1234")
    assertion.assert_equal(34, action2.numeric(), "action numeric id 34")

    # =================================

    game = Latrunculi(8)
    state = game.start_state()
    dictionary = dict()
    dictionary[state.stringify()] = "wow"

    assertion.assert_equal("wow", dictionary[state.stringify()], "state hashing")

    # ==================================
    # Test performance evalution
    storage = ReplayStorage()
    for i in range(10):
        storage.save_perform_eval_data(i/10)

    test_t = Thread(target=test_graph, args=(storage,))
    test_t.start()

    Graph.run(title="Test stuff", x_label="Step", y_label="Win ratio")
