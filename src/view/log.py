"""
------------------------------------------------------------------------
log: Log stuff, models (neural & mcts) and board to console and/or file.
------------------------------------------------------------------------
"""
from sys import argv

debug = "-d" in argv

def log(val):
    global debug
    if debug:
        print(val, flush=True)
