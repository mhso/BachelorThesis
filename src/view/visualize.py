"""
--------------------------------------------
visualize: Draw board state and other stuff.
--------------------------------------------
"""

import numpy as np
import tkinter as tk

from tkinter import ttk
from tkinter.messagebox import showinfo
from model.state import State, Action

import threading
from time import sleep
from view.log import log

# from FakeTestClasses import *

class Gui():
    game        = None
    state       = None
    root        = None
    canvas      = None
    listener    = None
    active      = True

    # List for keeping track of active valid mouse clicks
    mouseclick_move_list = None

    # Variables for board grid placement and design
    left_space  = 50
    top_space   = 50
    field_size  = 55

    pblt = None
    pbl = None
    pblc = None
    pwh = None
    pwht = None
    pwhc = None
    pbla = None
    pmar = None

    def __init__(self, game):
        game.register_observer(self)
        self.mouseclick_move_list = []
        self.game = game
        self.state = game.start_state()
        self.init()

    def notify(self, observable, *args, **kwargs):
        log("Got {}, {} {}".format(args, kwargs, observable))
        self.state = observable.actions(self.state)
        self.update(self.state)

    def run(self):
        self.root.mainloop()

    def init(self):
        self.init_window()
        self.load_graphics()
        self.init_board()

     # Creating main window
    def init_window(self):
        self.root = tk.Tk()
        self.root.bind("<Button 1>", self.getorigin)
        self.root.bind("<Destroy>", lambda e: self.close())
        self.root.title("Latrunculi - The Game")
        self.root.iconbitmap('./view/gfx/favicon.ico')
        self.canvas = tk.Canvas(self.root, width=540, height=680, background='lightgray')
        self.canvas.pack(expand=tk.YES, fill=tk.BOTH)

    # Initialize the board
    def init_board(self):
        self.widget_menubar(self.root)
        self.update(self.state)
        self.draw_axis_numbers(self.left_space, self.top_space, self.field_size, self.state.board)
        self.draw_status_text(canvas=self.canvas, msg="")

    def load_graphics(self):
        # load the .gif image file
        self.pblt = tk.PhotoImage(file='./view/gfx/pcs_bl_t.png')
        self.pbl = tk.PhotoImage(file='./view/gfx/pcs_bl.png')
        self.pblc = tk.PhotoImage(file='./view/gfx/pcs_bl_c.png')
        self.pwh = tk.PhotoImage(file='./view/gfx/pcs_wh.png')
        self.pwht = tk.PhotoImage(file='./view/gfx/pcs_wh_t.png')
        self.pwhc = tk.PhotoImage(file='./view/gfx/pcs_wh_c.png')
        self.pbla = tk.PhotoImage(file='./view/gfx/pcs_blank.png')
        self.pmar = tk.PhotoImage(file='./view/gfx/pcs_mark.png')

    # Return coordinat for mouse click
    def getorigin(self, eventorigin):
        x = eventorigin.x
        y = eventorigin.y

        coords = self.field_clicked(x, y, self.state.board, self.left_space, self.top_space, self.field_size)

        # if self.is_currentPlayer_piece(self.state.player, self.state.board[coords]):

        if self.is_currentPlayer_piece(self.state.player, self.state.board[coords]) and self.mouseclick_move_list == [] and self.has_legal_move(coords):
            self.mouseclick_move_list.append(coords)
            self.draw_status_text(self.canvas, "Selected source coords: ({})".format(coords))
        else:
            if self.mouseclick_move_list == [] and self.is_currentPlayer_piece(self.state.player, int(self.state.board[coords[0], coords[1]] * -0.5)):
                self.make_move(self.state, coords, coords)
            elif len(self.mouseclick_move_list) == 1:
                if self.mouseclick_move_list[0] == coords:
                    self.mouseclick_move_list.pop()
                elif self.is_currentPlayer_piece(self.state.player, self.state.board[coords]):
                    self.mouseclick_move_list.pop()
                    self.mouseclick_move_list.append(coords)
                else:
                    if self.is_legal_move(self.mouseclick_move_list[0], coords):
                        self.draw_status_text(self.canvas, "Selected destination coords: ({})".format(coords))
                        self.mouseclick_move_list.append(coords)

                        self.make_move(self.state, self.mouseclick_move_list[0], self.mouseclick_move_list[1])
                        self.mouseclick_move_list.clear()

            elif len(self.mouseclick_move_list) > 2:
                self.mouseclick_move_list.pop()

        log("mouseclick_move_list\n{}".format(self.mouseclick_move_list))

        self.update(self.state)

    # Confirms if a move i legal
    def is_legal_move(self, source_coords, dest_coords):
        for action in self.game.actions(self.state):
            if action.source == source_coords and action.dest == dest_coords:
                return True
        return False

    def has_legal_move(self, source_coords):
        for action in self.game.actions(self.state):
            if action.source == source_coords:
                return True
        return False

    def hello(self):
        print("hello!")

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
    def draw_axis_numbers(self, left_space, top_space, field_size, board):
        textcolor   = "darkblue"
        no_of_rows    = board.shape[0]
        no_of_cols    = board.shape[1]

        # Draw row numbers on canvas
        rt = 10+top_space
        for row in range(0, no_of_rows):
            self.canvas.create_text(left_space-10, rt+20, fill=textcolor, font="Courier 20", text=row)
            rt = rt + field_size

        # Draw column numbers on canvas
        ct = 10+left_space
        for col in range(0, no_of_cols):
            self.canvas.create_text(ct+20, top_space-10, fill=textcolor, font="Courier 20", text=col)
            ct = ct + field_size

    def draw_status_text(self, canvas, msg):
        canvas.create_rectangle(50, 510, 490, 650, fill='white')
        text_player_info = "Player1 is white, Player2 is black"
        # text_current_player = "Currentplayer is: {}".format(self.player_color(self.player))
        text_current_player = "Waiting for {}, please move a piece...".format(self.player_color(self.state.player))
        text = "{}\n{}\n{}".format(text_player_info, text_current_player, msg)
        canvas.create_text(60,515, fill="black", font="Courier 10", text=text, anchor=tk.NW)

    def player_color(self, player):
        if player:
            return "White"
        else:
            return "Black"

    # Returns image variable
    def select_piece_type(self, value):
        switcher = {
        -2: self.pblt,
        -1: self.pbl,
        0: self.pbla,
        1: self.pwh,
        2: self.pwht,
        }
        return switcher.get(value,"Invalid value option for select_piece_type")

    # Draw board and place pieces
    def draw_board_grid(self, board):
        canvas      = self.canvas
        field_size   = self.field_size
        left_space  = self.left_space
        top_space   = self.top_space
        gridcolor   = "black"
        no_of_rows    = board.shape[0]
        no_of_cols    = board.shape[1]
        py          = self.top_space
        px2         = self.left_space
        hlen        = no_of_rows*field_size+left_space
        vlen        = no_of_cols*field_size+top_space

        for y in range(no_of_rows):
            px = left_space
            # Draw vertical lines (column)
            canvas.create_line(px2, top_space, px2, vlen, fill=gridcolor)
            
            for x in range(no_of_cols):

                px = px + field_size
                
                # Draw horizontal lines (row)
                canvas.create_line(left_space, py, hlen, py, fill=gridcolor)
            py  = py + field_size
            px2 = px2 + field_size

        # Draw last horizontal lines (row)
        canvas.create_line(left_space, py, hlen, py, fill=gridcolor)

        # Draw last vertical lines (column)
        canvas.create_line(px2, top_space, px2, vlen, fill=gridcolor)

    # Draw board and place pieces
    def draw_board(self, board):
        canvas      = self.canvas
        field_size   = self.field_size
        left_space  = self.left_space
        top_space   = self.top_space
        # gridcolor   = "black"
        no_of_rows    = board.shape[0]
        no_of_cols    = board.shape[1]
        py          = self.top_space
        px2         = self.left_space
        hlen        = no_of_rows*field_size+left_space
        vlen        = no_of_cols*field_size+top_space
        
        #Hack, clear canvas
        canvas.create_rectangle(50, 50, hlen, vlen, fill='lightgray')

        for y in range(no_of_rows):
            px = left_space
            
            for x in range(no_of_cols):
                val = board[y, x]
                
                # If piece on field, place piece image
                if val != 0:
                    self.field(px, py, canvas, self.select_piece_type(val))
                
                # Mark if clicked by mouse
                if len(self.mouseclick_move_list) > 0 and self.mouseclick_move_list[0] == (y, x):
                    if val < 0:
                        self.field(px, py, canvas, self.pblc) # Mark black piece
                    else:
                        self.field(px, py, canvas, self.pwhc) # Mark white piece
                
                # Mark legal moves
                if len(self.mouseclick_move_list) > 0 and val == 0  and self.is_legal_move(self.mouseclick_move_list[0], (y, x)):
                    self.field(px, py, canvas, self.pmar)

                px = px + field_size

            py  = py + field_size
            px2 = px2 + field_size


    # Check wheather (white) piece is owned by currentPlayer one
    def is_currentPlayer_piece(self, player, value):

            if (value < 0 and player == 0) or (value > 0 and player == 1):
                return True
            else:
                return False

    def field_clicked(self, y, x, board, left_space, top_space, field_size):
        ymin = top_space
        for row in range(board.shape[0]):
            xmin = left_space
            ymax = ymin + field_size
            for col in range(board.shape[1]):
                xmax = xmin+field_size
                if x >= xmin and x < xmax and y >= ymin and y < ymax:
                    return col, row
                xmin = xmax
            ymin = ymin + field_size
        return (-1, -1)

    def update(self, state):
        self.state = state
        self.draw_board(state.board)
        self.draw_board_grid(state.board)
        self.draw_status_text(self.canvas, "Nice move")
        log("Updated")

    def make_move(self, state, source, dest):
        """
        Move a piece from source to dest on the board.
        Get the new state, and notify any listener about
        the new state.
        """
        log("Moved from {} to {}".format(source, dest))

        result = self.game.result(state, Action(source, dest))
        self.state = result
        self.update(result)

        if self.listener is not None:
            self.listener.action_made(result)
            self.listener = None

    def add_action_listener(self, listener):
        """
        Called by main while the game loop is running.
        """
        self.listener = listener

    def close(self):
        self.active = False
        self.root.destroy()
