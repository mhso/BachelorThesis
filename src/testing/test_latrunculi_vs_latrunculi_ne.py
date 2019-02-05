from numpy.random import uniform
from time import time
from testing import assertion
from controller.latrunculi import Latrunculi
from controller.latrunculi_ne import Latrunculi_ne
from model.state import Action
from util.excelUtil import ExcelUtil
import numpy as np
import scipy


def run_iteration_timing_l_vs_l_ne_test():
    # TEST STUFF
    print("run iteration timing test Latrunculi vs. Latrunculi_ne")
    l_game = Latrunculi(8, 55)
    l_state = l_game.start_state()

    l_ne_game = Latrunculi_ne(8, 55)
    l_ne_state = l_ne_game.start_state()
    
    time_b = time()

    l_counter = 0
    l_ne_counter = 0
    l_terminal = False
    l_ne_terminal = False
    count_terminal = 2
    time_taken_l = 0
    time_taken_ne = 0
    while count_terminal > 0:
        if not l_terminal:

            if l_game.terminal_test(l_state):
                time_taken_l = time() - time_b
                print("Latrunculi Time taken to play out game: {} s".format(time_taken_l))
                print("Latrunculi Iterations: {}".format(l_counter))

                # Appending results to standard excel file "test_results.xlsx"
                l_row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "Latrunculi", l_counter, (time() - time_b))
                ExcelUtil.excel_append_row(l_row)

                count_terminal -= 1
                l_terminal = True
            else:
                l_actions = l_game.actions(l_state)
                l_l_rand = int(uniform(0, len(l_actions)))
                l_action = l_actions[l_l_rand]
                l_state = l_game.result(l_state, l_action)
                l_counter += 1

        if not l_ne_terminal:

            if l_ne_game.terminal_test(l_ne_state):
                time_taken_ne = time() - time_b
                print("Latrunculi_ne Time taken to play out game: {} s".format(time_taken_ne))
                print("Latrunculi_ne Iterations: {}".format(l_ne_counter))

                # Appending results to standard excel file "test_results.xlsx"
                l_ne_row = (ExcelUtil.get_datetime_str(), ExcelUtil.get_computer_hostname(), "Latrunculi_ne", l_ne_counter, (time() - time_b))
                ExcelUtil.excel_append_row(l_ne_row)

                count_terminal -= 1
                l_ne_terminal = True
            else:
                l_ne_actions = l_ne_game.actions(l_ne_state)
                l_ne_rand = int(uniform(0, len(l_ne_actions)))
                l_ne_action = l_ne_actions[l_ne_rand]
                l_ne_state = l_ne_game.result(l_ne_state, l_ne_action)
                l_ne_counter += 1
    return time_taken_l, time_taken_ne