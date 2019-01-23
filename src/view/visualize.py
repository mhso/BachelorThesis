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

# def color_pick(val) :
#     switcher = {
#         -2: "gray",
#         -1: "black",
#         0: "ivory2",
#         1: "white",
#         2: "yellow"
#     }
#     return switcher.get(val,"Invalid color option")

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
    


board = np.array([[0,0,-1,-1,0,0,0,0],[-1,0,0,0,0,0,0,0],[1,0,-1,0,1,0,0,0],[1,0,0,0,0,0,-1,1],[0,1,0,0,0,0,0,-2],[0,0,0,0,-1,0,0,1],[0,0,0,0,0,0,0,1],[0,-1,0,-1,2,-1,0,0]])

"""
board_size = 8
rand_seed = 42
game = Latrunculi(board_size, rand_seed)
board = Game.start_state().board
"""

# load the .gif image file
pblt = PhotoImage(file='pcs_bl_t.png')
pbl = PhotoImage(file='pcs_bl.png')
pwh = PhotoImage(file='pcs_wh.png')
pwht = PhotoImage(file='pcs_wh_t.png')
pbla = PhotoImage(file='pcs_blank.png')

def field(x, y, canvas, img) :
    canvas.create_image(x, y, image=img, anchor=NW)
    return 

noOfRows = board.shape[0]
noOfCols = board.shape[1]

xpadding = 50
ypadding = 50
fieldsize = 55
gridcolor = "black"
textcolor = "darkblue"
rlen = noOfRows*fieldsize+ypadding
clen = noOfCols*fieldsize+xpadding

py = ypadding

rt = 10+ypadding
ct = 10+xpadding

# Draw row numbers on canvas
for y in range(0, noOfRows) :
    canvas.create_text(xpadding-10,rt+20,fill=textcolor,font="Courier 20",text=y)
    rt=rt+fieldsize

# Draw column numbers on canvas
for x in range(0, noOfRows) :
    canvas.create_text(ct+20,ypadding-10,fill=textcolor,font="Courier 20",text=x)
    ct=ct+fieldsize

def select_piece_type(value) :
    # if val == -2 :
    #     img = pblt
    # elif val == -1 :
    #     img = pbl
    # elif val == 1 :
    #     img = pwh
    # elif val == 2 :
    #     img = pwht
    # else :
    #     img = pbla
    # return img
    switcher = {
    -2: pblt,
    -1: pbl,
    0: pbla,
    1: pwh,
    2: pwht
    }
    return switcher.get(value,"Invalid value option for select_piece_type")

# Draw board and place pieces
for y in range(0, noOfRows) :
        px = xpadding
        canvas.create_line(ypadding,px,clen,px, fill=gridcolor)
        for x in range(0, noOfCols) :
            # canvas_field(x, y, board[x,y])
            val = board[x,y]
            # if val == -2 :
            #     img = pblt
            # elif val == -1 :
            #     img = pbl
            # elif val == 1 :
            #     img = pwh
            # elif val == 2 :
            #     img = pwht
            # else :
            #     img = pbla
            img = select_piece_type(val)
            if val != 0 :
                field(px, py, canvas, img)
            mystr = '(%(x)s,%(y)s)'% {'x':x, 'y':y}
            # if debug :
            #   canvas.create_text(px+25,py+30,fill="white",font="Courier 9 bold",text=mystr)
            px = px+55
            
            canvas.create_line(ypadding,px,clen,px, fill=gridcolor)
        canvas.create_line(py,xpadding,py,rlen, fill=gridcolor)
        py = py+55
canvas.create_line(py,xpadding,py,rlen, fill=gridcolor)



root.mainloop()