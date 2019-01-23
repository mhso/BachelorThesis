"""
--------------------------------------------
visualize: Draw board state and other stuff.
--------------------------------------------
"""

import numpy as np
import tkinter as tk

from tkinter import ttk
from tkinter.messagebox import showinfo

# from controller.game import Game
# from model.state import State, Action

click_x         = -1
click_y         = -1
click_x_last    = -1
click_y_last    = -1
clickCount      = -1

####################################################################
# Tempory variables for testing
board = np.array([[0,0,-1,-1,0,0,0,0],[-1,0,0,0,0,0,0,0],[1,0,-1,0,1,0,0,0],[1,0,0,0,0,0,-1,1],[0,1,0,0,0,0,0,-2],[0,0,0,0,-1,0,0,1],[0,0,0,0,0,0,0,1],[0,-1,0,-1,2,-1,0,0]])
currentPlayer = 1

class Action:
    source = 0, 0
    dest = 0, 0

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

actionlist = [  Action((2,0),(2,1)),
                Action((2,4),(1,4)), Action((2,4),(2,3)), Action((2,4),(2,5)), Action((2,4),(3,4)),
                Action((3,0),(3,1)), Action((3,0),(4,0)),
                Action((3,7),(2,7)),
                Action((4,1),(3,1)), Action((4,1),(4,0)), Action((4,1),(4,2)), Action((4,1),(5,1)),
                Action((5,7),(5,6)),
                Action((6,7),(6,6)), Action((6,7),(7,7))
                ]   
####################################################################

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

# Return coordinat for mouse click
def getorigin(eventorigin):
    global board
    x = eventorigin.x
    y = eventorigin.y
    clicksaver(x, y)
    coords = field_clicked(x, y, board, left_space, top_space, fieldsize)
    if not is_currentPlayer1_piece(currentPlayer, board[coords]) :
        coords = (-1,-1)
    board = unmark_board(board, coords)
    board = mark_unmark_piece(board, coords)
    bx, by = coords
    draw_status_text(canvas, 'Selected: (%(x)s,%(y)s)'%{'x':bx, 'y':by})

    if is_currentPlayer1_piece(currentPlayer, board[coords]) and not (click_x_last == -1 or click_y_last == -1 ) :
        (x2, y2) = field_clicked(x, y, board, left_space, top_space, fieldsize)
        draw_status_text(canvas, 'Move from: (%(x)s,%(y)s) to (%(x2)s,%(y2)s)'%{'x':bx, 'y':by, 'x2':x2, 'y2':y2})
    draw_board(board)

# Confirms if a move i legal
def isLegalMove(actionlist, source_coords, dest_coords) :
    for action in actionlist :
        if action.source == source_coords and action.dest == dest_coords :
            return True
    return False


# Creating main window
root = tk.Tk()
root.bind("<Button 1>",getorigin)
root.title("Latrunculi - The Game")
root.iconbitmap('favicon.ico')

canvas = tk.Canvas(root,width=540,height=680,background='lightgray')
canvas.pack(expand=tk.YES, fill=tk.BOTH)

def hello():
    print ("hello!")

def menubar_help_about_popup() :
    showinfo("About", "This great game of Latrunculi is made as addition to our bachelor project at IT-University of Copenhagen, please enjoy.\n\n ITU 2019 Denmark\n\n Alexander M. Hansen <alhm@itu.dk>\n Mikkel H. Sørensen <mhso@itu.dk>\n Frank Andersen <fand@itu.dk>\n ")

# Menubar
def widget_menubar(root) :
    # create a toplevel menu
    menubar = tk.Menu(root)

    # create a pulldown menu, and add it to the menu bar
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open replay", command=hello)
    filemenu.add_command(label="Save replay", command=hello)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    # create more pulldown menus
    optionmenu = tk.Menu(menubar, tearoff=0)
    optionmenu.add_command(label="Human vs. AI", command=hello)
    optionmenu.add_command(label="AI vs. AI", command=hello)
    menubar.add_cascade(label="Options", menu=optionmenu)

    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="About", command=menubar_help_about_popup)
    menubar.add_cascade(label="Help", menu=helpmenu)

    # display the menu
    root.config(menu=menubar)

widget_menubar(root)

# Places images on canvas at position
def field(x, y, canvas, img_filename) :
    canvas.create_image(x, y, image=img_filename, anchor=tk.NW) 




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


def draw_status_text(canvas, msg) :
    canvas.create_rectangle(50, 510, 490, 650, fill='white')
    canvas.create_text(60,515, fill="black", font="Courier 10", text="currentPlayer1 is white, currentPlayer2 is black", anchor=tk.NW)
    canvas.create_text(60,530, fill="black", font="Courier 10", text=msg, anchor=tk.NW)


# load the .gif image file
pblt    = tk.PhotoImage(file='pcs_bl_t.png')
pbl     = tk.PhotoImage(file='pcs_bl.png')
pblc    = tk.PhotoImage(file='pcs_bl_c.png')
pwh     = tk.PhotoImage(file='pcs_wh.png')
pwht    = tk.PhotoImage(file='pcs_wh_t.png')
pwhc    = tk.PhotoImage(file='pcs_wh_c.png')
pbla    = tk.PhotoImage(file='pcs_blank.png')
pmar    = tk.PhotoImage(file='pcs_mark.png')

# Returns image variable
def select_piece_type(value) :
    switcher = {
    -3: pblc,
    -2: pblt,
    -1: pbl,
    0: pbla,
    1: pwh,
    2: pwht,
    3: pwhc
    }
    return switcher.get(value,"Invalid value option for select_piece_type")

# Draw board and place pieces
def draw_board(board) :

    gridcolor   = "black"
    noOfRows    = board.shape[0]
    noOfCols    = board.shape[1]
    py      = top_space
    px2     = left_space
    hlen    = noOfRows*fieldsize+left_space
    vlen    = noOfCols*fieldsize+top_space
    markedCoords = (-1,-1)

    #Hack, clear canvas
    canvas.create_rectangle(50, 50, hlen, vlen, fill='lightgray')

    for y in range(0, noOfRows) :
        for x in range(0, noOfCols) :               
            if board[x,y] == -3 or board[x,y] == 3 :
                markedCoords = (x,y)
                

    for y in range(0, noOfRows) :
        px = left_space
        
        # Draw vertical lines (column)
        canvas.create_line(px2, top_space, px2, vlen, fill=gridcolor)
        
        for x in range(0, noOfCols) :
            val = board[x,y]
            
            # If piece on field, place piece image
            if val != 0 :
                field(px, py, canvas, select_piece_type(val))
            
            # Mark lega moves
            if not markedCoords == (-1,-1) and val == 0  and isLegalMove(actionlist, markedCoords, (x,y)) :
                field(px, py, canvas, pmar)

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

# Flips a 
def mark_unmark_piece(board, coords) :
    val = board[coords]
    if (val == -1) :
        board[coords] = -3
    elif (val == -3) :
        board[coords] = -1
    if val == 1 :
        board[coords] = 3
    elif (val == 3) :
        board[coords] = 1
    return board

def unmark_board(board, exclude_coords=(-1,-1)) :
    for y in range(0, board.shape[1]) :
        for x in range(0, board.shape[1]) :
            if ((x,y) == exclude_coords) :
                continue
            if (board[x,y] == -3) :
                board[x,y] = -1
            if (board[x,y] == 3) :
                board[x,y] = 1
    return board

# Check wheather (white) piece is owned by currentPlayer one
def is_currentPlayer1_piece(currentPlayer, value) :
        if (currentPlayer == 1 and value > 0) :
            return True
        else :
            return False

def field_clicked(x,y, board, left_space, top_space, fieldsize) :
    #print("field_clicked")
    #print(x, y)
    
    ymin = top_space
    for row in range(0, board.shape[0]) :
        xmin = left_space
        ymax = ymin+fieldsize
        for col in range(0, board.shape[1]) :
            xmax = xmin+fieldsize
            # print(col, row)
            # print(xmin, xmax, ymin, ymax)
            if (x >= xmin and x < xmax and y >= ymin and y < ymax) :
                #print("found")
                #print(col, row)
                # print("\n")
                return (col, row)
            xmin = xmax
        ymin = ymin+fieldsize
    return (-1,-1)


draw_board(board)

draw_axis_numbers(left_space, top_space, fieldsize, board)
draw_status_text(canvas, 'Waiting for currentPlayer1, please move a piece...')

root.mainloop()