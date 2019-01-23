"""
--------------------------------------------
visualize: Draw board state and other stuff.
--------------------------------------------
"""

import numpy as np
import tkinter as tk

# def load_src(name, fpath):
#     import os, imp
#     p = fpath if os.path.isabs(fpath) \
#         else os.path.join(os.path.dirname(__file__), fpath)
#     return imp.load_source(name, p)

# load_src("game", "../controller/game.py")
# import game
# load_src("latrunculi", "../controller/latrunculi.py")

def color_pick(val) :
    switcher = {
        -2: "gray",
        -1: "black",
        0: "ivory2",
        1: "white",
        2: "yellow"
    }
    return switcher.get(val,"Invalid color option")

window = tk.Tk()

root = tk.Tk()
root.title("Latrunculi - The Game")
frame = tk.Frame(root)
frame.pack()

topframe = tk.Frame(root)
topframe.pack(side=TOP)

bottomframe = tk.Frame(root)
bottomframe.pack( side = BOTTOM )



def canvas_field(rowNo, colNo, val) :
    #print (val)
    #print (color_pick(val))
    canvas = tk.Canvas(window,width=50,height=50,background=color_pick(val))
    canvas.grid(row=rowNo,column=colNo)
    img = tk.PhotoImage(file='pcs_black.png')
    canvas.create_image(50, 50, image=img)


board = np.array([[-2,0,0,0,0,0,0,0],[-1,0,0,0,0,0,0,0],[1,0,0,0,0,0,0,0],[2,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]])

"""
board_size = 8
rand_seed = 42
game = Latrunculi(board_size, rand_seed)
board = Game.start_state().board
"""

noOfRows = board.shape[0]
noOfCols = board.shape[1]

print (noOfRows)
print (noOfCols)


for y in range(0, noOfRows) :
        for x in range(0, noOfCols) :
            canvas_field(x, y, board[x,y])
            # print (board[x,y])



window.mainloop()


# root = tk.Tk()
# canvas = tk.Canvas(root, width=500, height=500)
# canvas.pack()
# img = tk.PhotoImage(file='pcs_black.png')
# canvas.create_image(250, 250, image=img)
# root.mainloop()