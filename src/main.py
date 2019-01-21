"""
----------------------------------------
main: Run game iterations and do things.
----------------------------------------
"""
from controller.latrunculi import Latrunculi

TEST = Latrunculi(8, 42)
print(TEST.start_state())
