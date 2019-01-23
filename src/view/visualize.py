"""
--------------------------------------------
visualize: Draw board state and other stuff.
--------------------------------------------
"""

import numpy as np
import tkinter as tk
from tkinter import *

def getorigin(eventorigin):
      global x,y
      x = eventorigin.x
      y = eventorigin.y
      print(x,y)

root = tk.Tk()
root.bind("<Button 1>",getorigin)

def color_pick(val) :
    switcher = {
        -2: "gray",
        -1: "black",
        0: "ivory2",
        1: "white",
        2: "yellow"
    }
    return switcher.get(val,"Invalid color option")

def pick_imgfile_pick(value) :
    switcher = {
        -2: PhotoImage(file="pcs_bl.png"),
        -1: PhotoImage(file="pcs_bl_t.png"),
        0: PhotoImage(file="pcs_blank.png"),
        1: PhotoImage(file="pcs_wh.png"),
        2: PhotoImage(file="pcs_wh_t.png")
    }
    return switcher.get(value,"Invalid value option for pick_imgfile_pick")

root.title("Latrunculi - The Game")
canvas = tk.Canvas(root,width=500,height=500,background='gray')
canvas.pack(expand=YES, fill=BOTH)

# def canvas_field(rowNo, colNo, val) :
#     print (val)
#     print (color_pick(val))
#     canvas = tk.Canvas(root,width=50,height=50,background=color_pick(val))
#     img = tk.PhotoImage(file='pcs_black.png')
#     canvas.create_image(50, 50, image=img)
#     canvas.grid(row=rowNo,column=colNo)
    


board = np.array([[-1,0,-1,-1,0,0,0,0],[-1,0,0,0,0,0,0,0],[1,0,-1,0,1,0,0,0],[1,0,0,0,0,0,-1,1],[0,1,0,0,0,0,0,-2],[0,0,0,0,-1,0,0,1],[0,0,0,0,0,0,0,1],[0,-1,0,-1,2,-1,0,0]])

"""
board_size = 8
rand_seed = 42
game = Latrunculi(board_size, rand_seed)
board = Game.start_state().board
"""

# load the .gif image file
a1 = PhotoImage(file='pcs_bl_t.png')
a2 = PhotoImage(file='pcs_bl.png')
a3 = PhotoImage(file='pcs_wh.png')
a4 = PhotoImage(file='pcs_wh_t.png')
a5 = PhotoImage(file='pcs_blank.png')

def field(x, y, canvas, img) :
    canvas.create_image(x, y, image=img, anchor=NW)
    return 


noOfRows = board.shape[0]
noOfCols = board.shape[1]

rlen = noOfRows*55+10
clen = noOfCols*55+10

py = 10
for y in range(0, noOfRows) :
        px = 10
        canvas.create_line(10,px,clen,px, fill="black")
        for x in range(0, noOfCols) :
            # canvas_field(x, y, board[x,y])
            val = board[x,y]
            if val == -2 :
                img = a1
            elif val == -1 :
                img = a2
            elif val == 1 :
                img = a3
            elif val == 2 :
                img = a4
            else :
                img = a5

            if val != 0 :
                field(px, py, canvas, img)
            px = px+55
            # print (board[x,y])
            canvas.create_line(10,px,clen,px, fill="black")
        canvas.create_line(py,10,py,rlen, fill="black")
        py = py+55
canvas.create_line(py,10,py,rlen, fill="black")



root.mainloop()