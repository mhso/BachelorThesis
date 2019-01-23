"""
--------------------------------------------
visualize: Draw board state and other stuff.
--------------------------------------------
"""

import numpy as np
import tkinter as tk

click_x         = -1
click_y         = -1
click_x_last    = -1
click_y_last    = -1
clickCount      = -1

# Tempory board
board = np.array([[0,0,-1,-1,0,0,0,0],[-1,0,0,0,0,0,0,0],[1,0,-1,0,1,0,0,0],[1,0,0,0,0,0,-1,1],[0,1,0,0,0,0,0,-2],[0,0,0,0,-1,0,0,1],[0,0,0,0,0,0,0,1],[0,-1,0,-1,2,-1,0,0]])

def clicksaver(x, y) :
    global click_x, click_y, click_x_last, click_y_last, clickCount
    if (clickCount == 0) :
        click_x_last = click_x
        click_y_last = click_y
        click_x = x
        click_y = y
        clickCount = -1
    else :
        click_x_last = -1
        click_y_last = -1
        click_x = x
        click_y = y
        clickCount = 0
    print(x,y)
    print(click_x, click_y)
    print(click_x_last, click_y_last)


# Return coordinat for mouse click
def getorigin(eventorigin):
    x = eventorigin.x
    y = eventorigin.y
    clicksaver(x, y)
    field_clicked(x, y, board)
    #print(x,y)
    


# Places images on canvas at position
def field(x, y, canvas, img) :
    canvas.create_image(x, y, image=img, anchor=tk.NW)
    return 

# Creating main window
root = tk.Tk()
root.bind("<Button 1>",getorigin)
root.title("Latrunculi - The Game")

# Creating main canvas
canvas = tk.Canvas(root,width=540,height=700,background='lightgray')
canvas.pack(expand=tk.YES, fill=tk.BOTH)


# Setting up variables for board grid placement and design
left_space  = 50
top_space   = 50
fieldsize   = 55

# Draw axis fields nuumbers
def draw_axis_numbers(left_space, top_space, fieldsize, board) :
    textcolor   = "darkblue"
    noOfRows    = board.shape[0]
    noOfCols    = board.shape[1]
    # Draw row numbers on canvas
    rt = 10+top_space
    for row in range(0, noOfRows) :
        canvas.create_text(left_space-10, rt+20, fill=textcolor, font="Courier 20", text=row)
        rt=rt+fieldsize

    # Draw column numbers on canvas
    ct = 10+left_space
    for col in range(0, noOfCols) :
        canvas.create_text(ct+20, top_space-10, fill=textcolor, font="Courier 20", text=col)
        ct=ct+fieldsize

# load the .gif image file
pblt    = tk.PhotoImage(file='pcs_bl_t.png')
pbl     = tk.PhotoImage(file='pcs_bl.png')
pwh     = tk.PhotoImage(file='pcs_wh.png')
pwht    = tk.PhotoImage(file='pcs_wh_t.png')
pbla    = tk.PhotoImage(file='pcs_blank.png')

# Returns image variable
def select_piece_type(value) :
    switcher = {
    -2: pblt,
    -1: pbl,
    0: pbla,
    1: pwh,
    2: pwht
    }
    return switcher.get(value,"Invalid value option for select_piece_type")

def draw_board(board) :
    # Draw board and place pieces
    gridcolor   = "black"
    noOfRows    = board.shape[0]
    noOfCols    = board.shape[1]

    py      = top_space
    px2     = left_space
    hlen    = noOfRows*fieldsize+left_space
    vlen    = noOfCols*fieldsize+top_space
    for y in range(0, noOfRows) :
            px = left_space
            
            # Draw vertical lines (column)
            canvas.create_line(px2, top_space, px2, vlen, fill=gridcolor)
            
            for x in range(0, noOfCols) :
                val = board[x,y]
                
                # If piece on field, place piece image
                if val != 0 :
                    field(px, py, canvas, select_piece_type(val))
                
                #mystr = '(%(x)s,%(y)s)'% {'x':x, 'y':y}
                # if debug :
                #   canvas.create_text(px+25,py+30,fill="white",font="Courier 9 bold",text=mystr)
                px = px+fieldsize
                
                # Draw horizontal lines (row)
                canvas.create_line(left_space, py, hlen, py, fill=gridcolor)
            py  = py+fieldsize
            px2 = px2+fieldsize

    # Draw last horizontal lines (row)
    canvas.create_line(left_space, py, hlen, py, fill=gridcolor)

    # Draw last vertical lines (column)
    canvas.create_line(px2, top_space, px2, vlen, fill=gridcolor)
    board_upper_left = (left_space, top_space)
    board_lower_right =  (vlen, hlen)
    return (board_upper_left, board_lower_right)


def field_clicked(x,y,board) :
    # ux, uy = board_upper_left
    # lx, ly = board_lower_right
    # hlen = ux+55*8
    # vlen = uy+55*8
    fieldsize = 55

    print("field_clicked\n")
    print(x, y)
    ymin = 50
    xmin = 50
    for row in range(0, board.shape[0]) :
        
        ymax = ymin+55
        for col in range(0, board.shape[1]) :
            xmax = xmin+fieldsize
            print(col, row)
            print(xmin, xmin, ymin, ymax)
            if (x >= xmin and x < xmax and y >= ymin and y < ymax) :
                print("found\n")
                print(col, row)
                print("\n")
                return (col,row)
        xmin = xmin+fieldsize
    ymin = ymin+fieldsize
    return (-1,-1)




(board_upper_left, board_lower_right) = draw_board(board)

draw_axis_numbers(left_space, top_space, fieldsize, board)

root.mainloop()