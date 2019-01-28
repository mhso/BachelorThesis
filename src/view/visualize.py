"""
--------------------------------------------
visualize: Draw board state and other stuff.
--------------------------------------------
"""

import numpy as np
import tkinter as tk

from tkinter import ttk
from tkinter.messagebox import showinfo

import threading
from time import sleep

class Gui:
    game        = None
    board       = None
    player      = None
    # state       = None
    root        = None
    canvas      = None
    # Variables for mouse click handling
    click_x         = -1
    click_y         = -1
    click_x_last    = -1
    click_y_last    = -1
    clickCount      = -1

    # Variables for board grid placement and design
    left_space  = 50
    top_space   = 50
    fieldsize   = 55

    pblt = None
    pbl = None
    pblc = None
    pwh = None
    pwht = None
    pwhc = None
    pbla = None
    pmar = None

    def __init__(self, game):
        state = game.start_state() 
        (self.board, self.player) = state
        self.init()

    def init(self):
        self.init_window()
        self.load_graphics()
        self.init_board()
        self.root.mainloop()
    
     # Creating main window
    def init_window(self):
        self.root = tk.Tk()
        self.root.bind("<Button 1>",self.getorigin)
        self.root.title("Latrunculi - The Game")
        self.root.iconbitmap('gfx/favicon.ico')
        self.canvas = tk.Canvas(self.root,width=540,height=680,background='lightgray')
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

    # Initialize the board
    def init_board(self):
        self.widget_menubar(self.root)
        self.draw_board(self.board)
        self.draw_axis_numbers(self.left_space, self.top_space, self.fieldsize, self.board)
        self.draw_status_text(canvas=self.canvas, msg='Waiting for currentPlayer1, please move a piece...')

    def load_graphics(self):
        # load the .gif image file
        self.pblt    = tk.PhotoImage(file='gfx/pcs_bl_t.png')
        self.pbl     = tk.PhotoImage(file='gfx/pcs_bl.png')
        self.pblc    = tk.PhotoImage(file='gfx/pcs_bl_c.png')
        self.pwh     = tk.PhotoImage(file='gfx/pcs_wh.png')
        self.pwht    = tk.PhotoImage(file='gfx/pcs_wh_t.png')
        self.pwhc    = tk.PhotoImage(file='gfx/pcs_wh_c.png')
        self.pbla    = tk.PhotoImage(file='gfx/pcs_blank.png')
        self.pmar    = tk.PhotoImage(file='gfx/pcs_mark.png')

    def clicksaver(self, x, y):
        global click_x, click_y, click_x_last, click_y_last, clickCount
        if (self.clickCount == 0):
            click_x_last = self.click_x
            click_y_last = self.click_y
            click_x = x
            click_y = y
            clickCount = -1
        else:
            click_x_last = -1
            click_y_last = -1
            click_x = x
            click_y = y
            clickCount = 0
    
    # Return coordinat for mouse click
    def getorigin(self, eventorigin):
        left_space  = self.left_space
        top_space   = self.top_space
        fieldsize   = self.fieldsize
        x = eventorigin.x
        y = eventorigin.y
        self.clicksaver(x, y)
        coords = self.field_clicked(x, y, self.board, left_space, top_space, fieldsize)
        if not self.is_currentPlayer1_piece(self.player, self.board[coords]):
            coords = (-1,-1)
        board = self.unmark_board(self.board, coords)
        board = self.mark_unmark_piece(board, coords)
        bx, by = coords
        self.draw_status_text(self.canvas, 'Selected: (%(x)s,%(y)s)'%{'x':bx, 'y':by})

        if self.is_currentPlayer1_piece(self.player, board[coords]) and not (click_x_last == -1 or click_y_last == -1 ):
            (x2, y2) = self.field_clicked(x, y, board, left_space, top_space, fieldsize)
            self.draw_status_text(self.canvas, 'Move from: (%(x)s,%(y)s) to (%(x2)s,%(y2)s)'%{'x':bx, 'y':by, 'x2':x2, 'y2':y2})
        self.draw_board(board)

    # Confirms if a move i legal
    def is_legal_move(self, source_coords, dest_coords):
        for action in self.game.actions((self.board, self.player)):
            if action.source == source_coords and action.dest == dest_coords:
                return True
        return False

    def hello(self):
        print ("hello!")

    def menubar_help_about_popup(self):
        showinfo("About", "This great game of Latrunculi is made as addition to our bachelor project at IT-University of Copenhagen, please enjoy.\n\n ITU 2019 Denmark\n\n Alexander M. Hansen <alhm@itu.dk>\n Mikkel H. Sørensen <mhso@itu.dk>\n Frank Andersen <fand@itu.dk>\n ")

    # Menubar
    def widget_menubar(self, root):
        # create a toplevel menu
        menubar = tk.Menu(root)
        hello = self.hello
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
        helpmenu.add_command(label="About", command=self.menubar_help_about_popup)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # display the menu
        root.config(menu=menubar)

    # Places images on canvas at position
    def field(self, x, y, canvas, img_filename):
        canvas.create_image(x, y, image=img_filename, anchor=tk.NW) 

    # Draw axis fields nuumbers
    def draw_axis_numbers(self, left_space, top_space, fieldsize, board):
        textcolor   = "darkblue"
        noOfRows    = board.shape[0]
        noOfCols    = board.shape[1]
        # Draw row numbers on canvas
        rt = 10+top_space
        for row in range(0, noOfRows):
            self.canvas.create_text(left_space-10, rt+20, fill=textcolor, font="Courier 20", text=row)
            rt=rt+fieldsize

        # Draw column numbers on canvas
        ct = 10+left_space
        for col in range(0, noOfCols):
            self.canvas.create_text(ct+20, top_space-10, fill=textcolor, font="Courier 20", text=col)
            ct=ct+fieldsize

    def draw_status_text(self, canvas, msg):
        canvas.create_rectangle(50, 510, 490, 650, fill='white')
        canvas.create_text(60,515, fill="black", font="Courier 10", text="currentPlayer1 is white, currentPlayer2 is black", anchor=tk.NW)
        canvas.create_text(60,530, fill="black", font="Courier 10", text=msg, anchor=tk.NW)

    # Returns image variable
    def select_piece_type(self, value):
        switcher = {
        -3: self.pblc,
        -2: self.pblt,
        -1: self.pbl,
        0: self.pbla,
        1: self.pwh,
        2: self.pwht,
        3: self.pwhc
        }
        return switcher.get(value,"Invalid value option for select_piece_type")

    # Draw board and place pieces
    def draw_board(self, board):
        self.board = board
        canvas      = self.canvas
        fieldsize   = self.fieldsize
        left_space  = self.left_space
        top_space   = self.top_space
        gridcolor   = "black"
        noOfRows    = board.shape[0]
        noOfCols    = board.shape[1]
        py          = self.top_space
        px2         = self.left_space
        hlen        = noOfRows*fieldsize+left_space
        vlen        = noOfCols*fieldsize+top_space
        markedCoords = (-1,-1)
        
        #Hack, clear canvas
        canvas.create_rectangle(50, 50, hlen, vlen, fill='lightgray')

        for y in range(0, noOfRows):
            for x in range(0, noOfCols):               
                if board[x,y] == -3 or board[x,y] == 3:
                    markedCoords = (x,y)

        for y in range(0, noOfRows):
            px = left_space
            
            # Draw vertical lines (column)
            canvas.create_line(px2, top_space, px2, vlen, fill=gridcolor)
            
            for x in range(0, noOfCols):
                val = board[x,y]
                
                # If piece on field, place piece image
                if val != 0:
                    self.field(px, py, canvas, self.select_piece_type(val))
                
                # Mark lega moves
                if not markedCoords == (-1,-1) and val == 0  and self.is_legal_move(markedCoords, (x,y)):
                    self.field(px, py, canvas, self.pmar)

                #mystr = '(%(x)s,%(y)s)'% {'x':x, 'y':y}
                # if debug:
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

    # Flips a piece marked/unmarked or unmarked/marked
    def mark_unmark_piece(self, board, coords):
        val = board[coords]
        if (val == -1):
            board[coords] = -3
        elif (val == -3):
            board[coords] = -1
        if val == 1:
            board[coords] = 3
        elif (val == 3):
            board[coords] = 1
        return board

    def unmark_board(self, board, exclude_coords=(-1,-1)):
        for y in range(0, board.shape[1]):
            for x in range(0, board.shape[1]):
                if ((x,y) == exclude_coords):
                    continue
                if (board[x,y] == -3):
                    board[x,y] = -1
                if (board[x,y] == 3):
                    board[x,y] = 1
        return board

    # Check wheather (white) piece is owned by currentPlayer one
    def is_currentPlayer1_piece(self, player, value):
            if (player == 1 and value > 0):
                return True
            else:
                return False

    def field_clicked(self, x,y, board, left_space, top_space, fieldsize):  
        ymin = top_space
        for row in range(0, board.shape[0]):
            xmin = left_space
            ymax = ymin+fieldsize
            for col in range(0, board.shape[1]):
                xmax = xmin+fieldsize
                if (x >= xmin and x < xmax and y >= ymin and y < ymax):
                    return (col, row)
                xmin = xmax
            ymin = ymin+fieldsize
        return (-1,-1)

    def update(self, state):
        self.board = state.board
        self.player = State.player

class myThread (threading.Thread):
    game = None

    def __init__(self, threadID, name, counter, game):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.game = game

    def run(self):
        Gui(game=self.game)

####################################################################
# Tempory variables for testing
# board = np.array([[0,0,-1,-1,0,0,0,0],[-1,0,0,0,0,0,0,0],[1,0,-1,0,1,0,0,0],[1,0,0,0,0,0,-1,1],[0,1,0,0,0,0,0,-2],[0,0,0,0,-1,0,0,1],[0,0,0,0,0,0,0,1],[0,-1,0,-1,2,-1,0,0]])
# currentPlayer = 1

class Action:
    source = 0, 0
    dest = 0, 0

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

class State:
    board = []
    player = True

    def __init__(self, board, player):
        self.board = board
        self.player = player

    def __str__(self):
        player = "White" if self.player else "Black"
        return "[State: \nPlayer turn = " + player + "\nBoard =\n" + str(self.board) + "\n]"

    def numeric(self):
        return hash(str(self.board))

# actionsList2 = [  Action((2,0),(2,1)),
#                 Action((2,4),(1,4)), Action((2,4),(2,3)), Action((2,4),(2,5)), Action((2,4),(3,4)),
#                 Action((4,0),(3,0)), Action((4,0),(5,0)),
#                 Action((3,7),(2,7)),
#                 Action((4,1),(3,1)), Action((4,1),(4,0)), Action((4,1),(4,2)), Action((4,1),(5,1)),
#                 Action((5,7),(5,6)),
#                 Action((6,7),(6,6)), Action((6,7),(7,7))
#                 ] 



class Game:

    actionslist = []

    def start_state(self):
        """
        Returns starting state for the game.
        """
        board      = np.array([[0,0,-1,-1,0,0,0,0],
                                            [-1,0,0,0,0,0,0,0],
                                            [1,0,-1,0,1,0,0,0],
                                            [1,0,0,0,0,0,-1,1],
                                            [0,1,0,0,0,0,0,-2],
                                            [0,0,0,0,-1,0,0,1],
                                            [0,0,0,0,0,0,0,1],
                                            [0,-1,0,-1,2,-1,0,0]])
        player = 1

        return State(board, player)

    def player(self, state):
        """
        Returns who’s turn it is given a state. True for white, False for black.
        """
        pass

    def actions(self, state):
        """
        Return list of legal moves for the given state.
        """
        actionsList = [Action((2,0),(2,1)),
                            Action((2,4),(1,4)), Action((2,4),(2,3)), Action((2,4),(2,5)), Action((2,4),(3,4)),
                            Action((3,0),(3,1)), Action((3,0),(4,0)),
                            Action((3,7),(2,7)),
                            Action((4,1),(3,1)), Action((4,1),(4,0)), Action((4,1),(4,2)), Action((4,1),(5,1)),
                            Action((5,7),(5,6)),
                            Action((6,7),(6,6)), Action((6,7),(7,7))
                            ]
        return actionsList

    def result(self, state, action):
        """
        Returns the state that results from doing action 'a' in state 's'.
        """
        board      = np.array([[0,0,-1,-1,0,0,0,0],
                                    [-1,0,0,0,0,0,0,0],
                                    [1,0,-1,0,1,0,0,0],
                                    [1,0,0,0,0,0,-1,1],
                                    [0,1,0,0,0,0,0,-2],
                                    [0,0,0,0,-1,0,0,1],
                                    [0,0,0,0,0,0,0,1],
                                    [0,-1,0,-1,2,-1,0,0]])

        return State(board, 1)

    def terminal_test(self, state):
        """
        Return True if the given state is a terminal state, meaning that the game is over, False otherwise.
        """
        pass


    def utility(self, state, player):
        """
        If the given player has lost, return 0, else return 1
        """

####################################################################

game = Game()

# Create new threads
thread1 = myThread(1, "Thread-1", 1, game)

# Start new Threads
thread1.start()

# from controller.game import Game
# from model.state import State, Action

