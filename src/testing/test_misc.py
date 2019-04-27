from threading import Thread
from time import sleep
from testing import assertion
from model.state import Action, State
from model.storage import ReplayStorage
from controller.latrunculi import Latrunculi
from controller.connect_four import Connect_Four
from view.graph import Graph
from controller.self_play import evaluate_against_ai, get_ai_algorithm
from config import Config

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

    # =================================
    # Test self-play performance evaluation.
    game = Connect_Four(6)
    as_white = evaluate_against_ai(game, get_ai_algorithm("Random", game), get_ai_algorithm("Random", game), True, 5, Config, None)
    as_black = evaluate_against_ai(game, get_ai_algorithm("Random", game), get_ai_algorithm("Random", game), False, 5, Config, None)
    print(as_white)
    print(as_black)
