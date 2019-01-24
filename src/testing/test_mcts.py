from controller.mcts import MCTS
from controller.latrunculi import Latrunculi

def run_tests():
    print("-=-=-=- MCTS TESTS -=-=-=-")
    # Test selection.
    game = Latrunculi(8)
    mcts = MCTS(game)
    state = game.start_state()

    selected = mcts.select(state)
    print(selected)

    # =================================
