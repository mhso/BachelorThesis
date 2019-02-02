"""
---------------------------------------------------------------------
latrunculi: Subclass of game. Implements game methods for latrunculi.
---------------------------------------------------------------------
"""
import numpy as np
from controller.game import Game
from model.state import State, Action
from enum import Enum

class Action_Move(Enum):
    UP_LEFT = 1
    UP = 2
    UP_RIGHT = 3
    LEFT = 4
    CENTER = 5
    RIGHT = 6
    DOWN_LEFT = 7
    DOWN = 8
    DOWN_RIGHT = 9

class Field_Enum(Enum):
    BLACK_TRAPPED = -2
    BLACK = -1
    NONE = 0
    WHITE = 1
    WHITE_TRAPPED = 2

class Latrunculi_s(Game):
    size = 8
    init_state = None

    board = None
    board_no_of_rows = -1
    board_no_of_cols = -1
    

    def populate_board(self, seed):
        board = np.zeros((self.size, self.size), 'b')
        num_pieces = int((self.size * self.size) / 2)

        if seed is not None:
            # Generate random positions for pieces
            np.random.seed(seed)
            squares = np.arange(0, self.size * self.size)
            np.random.shuffle(squares)

            # Populate board with equal amount of white and black pieces
            for i in range(num_pieces):
                num = squares[i]
                X = int(num / self.size)
                Y = int(num % self.size)
                piece = 1 if i < num_pieces/2 else -1

                board[X][Y] = piece
        else:
            # Position pieces as a 'Chess formation'.
            board[:][0:2] = -1
            board[:][-2:] = 1

        self.init_state = State(board, True)
        self.board_no_of_rows = board.shape[0]
        self.board_no_of_cols = board.shape[1]

    def __init__(self, size, start_seed=None):
        Game.__init__(self)
        self.size = size
        self.populate_board(start_seed)
    
    def notify_observers(self, *args, **kwargs):
        for observer in self.__observers:
            observer.notify(self, *args, **kwargs)

    def start_state(self):
        super.__doc__
        return self.init_state

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        # current_player = -1
        # enemy_captured = 2
        # player_color = Field_Enum.BLACK
        # opponent_color = Field_Enum.WHITE
        # if state.player:
        #     current_player = 1 #White
        #     enemy_captured = -2 #Black
        #     player_color = Field_Enum.WHITE
        #     opponent_color = Field_Enum.BLACK

        player_color = self.player_color(state.player)

        actionsList = [] #we might have to add a pass option???

        self.board = state.board
        
        for y in range(self.board_no_of_rows):
            for x in range(self.board_no_of_cols):
                
                if self.field_value((y, x)) == player_color:

                    # self.append_list_if_valid(actionsList, x, y, y-1, x-1)
                    self.append_list_if_valid(player_color, actionsList, (y, x), (y-1, x))
                    # self.append_list_if_valid(board_no_of_rows, board_no_of_cols, board, actionsList, x, y, y-1, x+1)

                    self.append_list_if_valid(player_color, actionsList, (y, x), (y, x-1))
                    self.append_list_if_valid(player_color, actionsList, (y, x), (y, x+1))

                    # self.append_list_if_valid(actionsList, x, y, y+1, x-1)
                    self.append_list_if_valid(player_color, actionsList, (y, x), (y+1, x))
                    # self.append_list_if_valid(actionsList, x, y, y+1, x+1)

                    # board[y-1, x-1]     # Above left
                    # board[y-1, x]       # Above center
                    # board[y-1, x+1]     # Above right

                    # board[y, x-1]     # Midt left

                    # board[y, x]         # Midt center

                    # board[y, x+1]     # Midt right

                    # board[y+1, x-1]     # Below left
                    # board[y+1, x]     # Below center
                    # board[y+1, x+1]     # Below right

        # if actionsList == []:
        #     actionsList.append(None)
        return actionsList

    def is_within_board(self, coords):
        y, x = coords
        return 0 <= x and x < self.board_no_of_rows and 0 <= y and y < self.board_no_of_rows
    
    def is_empty_field(self, coords):
        return self.is_within_board(coords) and self.board[coords] == 0
    
    def append_list_if_valid(self, player_color, alist, coords_from, coords_to):
        if self.is_empty_field(coords_to) and not self.is_suicide_move(coords_from, coords_to, player_color):
            alist.append(Action(coords_from, coords_to))
    
    def is_suicide_move(self, coords_from, coords_to, player_color):
        move = self.get_direction(coords_from, coords_to)
        opponent_color = self.oppenent_player_color(player_color)
        # print("player_color: {}".format(player_color))
        # print("opponent_color: {}".format(opponent_color))
        

        if move == Action_Move.UP:
            return not self.valid_left_right(coords_to, player_color, opponent_color)

        elif move == Action_Move.LEFT:
            return not self.valid_up_down(coords_to, player_color, opponent_color)

        elif move == Action_Move.RIGHT:
            return not self.valid_up_down(coords_to, player_color, opponent_color)

        elif move == Action_Move.DOWN:
            return not self.valid_left_right(coords_to, player_color, opponent_color)

        return True

    def valid_left_right(self, coords, player_color, opponent_color):

        left = self.move_coords(Action_Move.LEFT, coords)
        right = self.move_coords(Action_Move.RIGHT, coords)
        if self.is_empty_field(left) or self.is_empty_field(right) or not self.is_within_board(left) or not self.is_within_board(right):
            # if coords == (3, 5): print("{} valid_left_right empty field or not within board".format(coords))
            return True
        else:
            if self.is_within_board(left) and self.is_within_board(right) and self.field_value(left) == opponent_color and self.field_value(right) == opponent_color:
                
                # left_left = self.move_coords(Action_Move.LEFT, left)
                # right_right = self.move_coords(Action_Move.RIGHT, right)
                # if self.is_within_board(left_left) and self.field_player(left_left) == player_color or self.is_within_board(right_right) and self.field_player(right_right) == player_color:
                #     return True
                #if coords == (3, 5): print("{} valid_left_right within board and not opponent colors".format(coords))
                return False
            else:
                #if coords == (3, 5): print("{} valid_left_right not within board or not opponent colors".format(coords))
                return True

    def valid_up_down(self, coords, player_color, opponent_color):
        
        up = self.move_coords(Action_Move.UP, coords)
        down = self.move_coords(Action_Move.DOWN, coords)
        if self.is_empty_field(up) or self.is_empty_field(down) or not self.is_within_board(up) or not self.is_within_board(down):
            if coords == (3, 5): print("{} valid_up_down empty field or not within board".format(coords))
            return True
        else:           
            if self.is_within_board(up) and self.is_within_board(down) and self.field_value(up) == opponent_color and self.field_value(down) == opponent_color:

                # up_up = self.move_coords(Action_Move.UP, up)
                # down_down = self.move_coords(Action_Move.DOWN, down)
                # if self.is_within_board(up_up) and self.field_player(up_up) == player_color or self.is_within_board(down_down) and self.field_player(down_down) == player_color:
                #     return True
                if coords == (3, 5): print("{} valid_up_down within board and not opponent colors".format(coords))
                return False
            else:
                if coords == (3, 5):
                    print("{} valid_up_down not within board or not opponent colors".format(coords))
                    print("player_color: {}".format(player_color))
                    print("self.field_value(up): {}".format(self.field_value(up)))
                    print("self.field_value(down): {}".format(self.field_value(down)))
                    print("opponent_color: {}".format(opponent_color))
                return True

    def field_player(self, coords):
            return self.field_player_color(self.field_value(coords))

    def field_value(self, coords):
        val = self.board[coords]
        if val == -2:
            return Field_Enum.BLACK_TRAPPED
        elif val == -1:
            return Field_Enum.BLACK
        elif val == 0:
            return Field_Enum.NONE
        elif val == 1:
            return Field_Enum.WHITE
        elif val == 2:
            return Field_Enum.WHITE_TRAPPED

    def field_player_color(self, value):
        if value == Field_Enum.BLACK_TRAPPED or value == Field_Enum.BLACK:
            return Field_Enum.BLACK
        elif value == Field_Enum.WHITE_TRAPPED  or value == Field_Enum.WHITE:
            return Field_Enum.WHITE
        else:
            return Field_Enum.NONE

    def move_coords(self, direction, coords):
        y, x = coords
        if direction == Action_Move.UP_LEFT:
            return (y-1, x-1)
        elif direction == Action_Move.UP:
            return (y-1, x)
        elif direction == Action_Move.UP_RIGHT:
            return (y-1, x+1)

        elif direction == Action_Move.LEFT:
            return (y, x-1)
        elif direction == Action_Move.CENTER:
            return (y, x)
        elif direction == Action_Move.RIGHT:
            return (y, x+1)

        elif direction == Action_Move.DOWN_LEFT:
            return (y+1, x)
        elif direction == Action_Move.DOWN:
            return (y+1, x)
        elif direction == Action_Move.DOWN_RIGHT:
            return (y+1, x)
        return None

    def get_direction(self, coords_from, coords_to):
        y_from, x_from = coords_from
        y_to, x_to = coords_to
        if y_from-1 == y_to and x_from-1 == x_to:
            return Action_Move.UP_LEFT
        elif y_from-1 == y_to and x_from == x_to:
            return Action_Move.UP
        elif y_from-1 == y_to and x_from+1 == x_to:
            return Action_Move.UP_RIGHT

        elif y_from == y_to and x_from-1 == x_to:
            return Action_Move.LEFT
        elif y_from == y_to and x_from == x_to:
            return Action_Move.CENTER
        elif y_from == y_to and x_from+1 == x_to:
            return Action_Move.RIGHT
        
        elif y_from+1 == y_to and x_from-1 == x_to:
            return Action_Move.DOWN_LEFT
        elif y_from+1 == y_to and x_from == x_to:
            return Action_Move.DOWN
        elif y_from+1 == y_to and x_from+1 == x_to:
            return Action_Move.DOWN_RIGHT
        return None

    def player_color(self, value):
        if value == 0:
            return Field_Enum.BLACK
        elif value == 1:
            return Field_Enum.WHITE
        else:
            return None

    def oppenent_player_color(self, player_color):
        if player_color == Field_Enum.BLACK:
            return Field_Enum.WHITE
        elif player_color == Field_Enum.WHITE:
            return Field_Enum.BLACK
        else: 
            return None

    def piece_color(self, value):
        if value < 0:
            return Field_Enum.BLACK
        elif value > 0:
            return Field_Enum.WHITE
        else:
            return Field_Enum.NONE

    def traverse(self, board, kernel):
        pass

    def result(self, state, action):
        super.__doc__
        if action is None:
            return State(state.board, (not state.player))
        source = action.source
        dest = action.dest
        current_player = -1 #Black
        enemy_player = 1
        if state.player:
            current_player = 1 #White
            enemy_player = -1

        newBoard = np.copy(state.board) #newBoard is the one that will be returned
        
        if state.board[source] == current_player: #if source is a piece owned by the current player
            if not source == dest: #check if source and dest are different 
                illegal_action = True
                for ac in self.actions(state):
                    if ac.source == source and ac.dest == dest:
                        illegal_action = False
                
                if illegal_action:
                    raise Exception("you have attempted an illegal move...")
                
                newBoard[source] = 0
                newBoard[dest] = current_player



                print("Lets move the piece")


            else:
                raise Exception("you attempted to move your piece, to the square where the piece started")
        elif state.board[source] == (enemy_player*2): #if source is an opponents captured piece
            if source == dest: #if source and dest is equal, remove opponents captured piece
                newBoard[source] = 0 #removed captured piece
            else:
                raise Exception("you have attempted to move an opponents captured piece...")
        else: #If none of the above, illegal move...
            raise Exception("you have attempted to move a piece that you do not own...")


        # if state.board[source[0]][source[1]] == current_player: #if source is a piece owned by the current player
        #     if source[0] != dest[0] or source[1] != dest[1]: #check if source and dest are different
        #         i = dest[0]
        #         j = dest[1]
        #         newBoard[i][j] = current_player #moves piece to destination (dest)
        #         newBoard[source[0]][source[1]] = 0 #removes piece from source
        #         workBoard = np.copy(newBoard) #workBoard is the one that is checked during the method

        #         #check if the move frees an opponents captured piece
        #         self.check_For_Freeing_Due_To_Move(source[0], source[1], newBoard, enemy_player)

        #         #check for suicide moves
        #         if (i-1) >= 0 and (i+1) < self.size: #check if possible suicide move is within board bounds NORTH/SOUTH
        #             if workBoard[i-1][j] == enemy_player and workBoard[i+1][j] == enemy_player: #check for suicide move NORTH/SOUTH
        #                 #NORTH
        #                 if (i-2) >= 0: #check if suicide move capture, is within board bounds NORTH
        #                     if workBoard[i-2][j] == current_player: #check for suicide move capture NORTH
        #                         newBoard[i-1][j] = enemy_player*2 #captures the oppenents piece NORTH
        #                         self.freed_Check_West_East_of_Piece((i-1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
        #                 #SOUTH
        #                 if (i+2) < self.size: #check if suicide move capture, is within board bounds SOUTH
        #                     if workBoard[i+2][j] == current_player: #check for suicide move capture SOUTH
        #                         newBoard[i+1][j] = enemy_player*2 #captures the oppenents piece SOUTH
        #                         #check for freeing of another piece
        #                         self.freed_Check_West_East_of_Piece((i+1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece

        #         if (j-1) >= 0 and (j+1) < self.size: #check if possible suicide move is within board bounds WEST/EAST
        #             if workBoard[i][j-1] == enemy_player and workBoard[i][j+1] == enemy_player: #check for suicide move WEST/EAST
        #                 #WEST
        #                 if (j-2) >= 0: #check if suicide move capture, is within board bounds WEST
        #                     if workBoard[i][j-2] == current_player: #check for suicide move capture WEST
        #                         newBoard[i][j-1] = enemy_player*2 #captures the oppenents piece WEST
        #                         self.freed_Check_North_South_of_Piece(i, (j-1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
        #                 #EAST
        #                 if (j+2) < self.size: #check if suicide move capture, is within board bounds EAST
        #                     if workBoard[i][j+2] == current_player: #check for suicide move capture EAST
        #                         newBoard[i][j+1] = enemy_player*2 #captures the oppenents piece EAST
        #                         self.freed_Check_North_South_of_Piece(i, (j+1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece

        #         #check for regular capture of enemies
        #         #NORTH
        #         if (i-2) >= 0: #check if possible regular capture is within board bounds NORTH
        #             if workBoard[i-1][j] == enemy_player and workBoard[i-2][j] == current_player: #check for regular capture NORTH
        #                 newBoard[i-1][j] = enemy_player*2 #capture the opponents piece NORTH
        #                 self.freed_Check_West_East_of_Piece((i-1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
        #         #SOUTH
        #         if (i+2) < self.size: #check if possible regular capture is within board bounds SOUTH
        #             if workBoard[i+1][j] == enemy_player and workBoard[i+2][j] == current_player: #check for regular capture SOUTH
        #                 newBoard[i+1][j] = enemy_player*2 #capture the opponents piece SOUTH
        #                 self.freed_Check_West_East_of_Piece((i+1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
        #         #WEST
        #         if (j-2) >= 0: #check if possible regular capture is within board bounds WEST
        #             if workBoard[i][j-1] == enemy_player and workBoard[i][j-2] == current_player: #check for regular capture WEST
        #                 newBoard[i][j-1] = enemy_player*2 #capture the opponents piece WEST
        #                 self.freed_Check_North_South_of_Piece(i, (j-1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
        #         #EAST
        #         if (j+2) < self.size: #check if possible regular capture is within board bounds EAST
        #             if workBoard[i][j+1] == enemy_player and workBoard[i][j+2] == current_player: #check for regular capture EAST
        #                 newBoard[i][j+1] = enemy_player*2 #capture the opponents piece EAST
        #                 self.freed_Check_North_South_of_Piece(i, (j+1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
        #     else:
        #         raise Exception("you attempted to move your piece, to the square where the piece started")
        # elif state.board[source[0]][source[1]] == (enemy_player*2): #if source is an opponents captured piece
        #     if source[0] == dest[0] and source[1] == dest[1]: #if source and dest is equal, remove opponents captured piece
        #         newBoard[source[0]][source[1]] = 0 #removed captured piece
        #     else:
        #         raise Exception("you have attempted to move an opponents captured piece...")
        # else: #If none of the above, illegal move...
        #     raise Exception("you have attempted to move a piece that you do not own...")
        return State(newBoard, (not state.player))

    # #checks whether moving a piece from its source, causes an enemys piece to be freed
    # def check_For_Freeing_Due_To_Move(self, i, j, board, enemy):
    #     if (i-1) >= 0: #check that we are within board bounds
    #         if self.check_For_Freeing((i-1), j, board): #checks piece NORTH of source
    #             board[i-1][j] = enemy #frees piece
    #     if (i+1) < self.size: #check that we are within board bounds
    #         if self.check_For_Freeing((i+1), j, board): #checks piece SOUTH of source
    #             board[i+1][j] = enemy #frees piece
    #     if (j-1) >= 0: #check that we are within board bounds
    #         if self.check_For_Freeing(i, (j-1), board): #checks piece WEST of source
    #             board[i][j-1] = enemy #frees piece
    #     if (j+1) < self.size: #check that we are within board bounds
    #         if self.check_For_Freeing(i, (j+1), board): #checks piece EAST of source
    #             board[i][j+1] = enemy #frees piece

    # #check for freed pieces to the WEST/EAST of the given piece
    # def freed_Check_West_East_of_Piece(self, i, j, board, current_player):
    #     if i >= 0 and i < self.size: #check if the given i is within the board bounds
    #         if (j-1) >= 0: #check if its within the board bounds WEST
    #             if self.check_For_Freeing((i), (j-1), board): #check for freed piece to the WEST of the captured NORTH/SOUTH piece
    #                 board[i][j-1] = current_player #frees currentPlayers Alligatus
    #         if (j+1) < self.size: #check if its within the board bounds EAST
    #             if self.check_For_Freeing((i), (j+1), board): #check for freed piece to the EAST of the captured NORTH/SOUTH piece
    #                 board[i][j+1] = current_player #frees currentPlayers Alligatus
    
    # #check for freed pieces to the NORTH/SOUTH of the given piece
    # def freed_Check_North_South_of_Piece(self, i, j, board, current_player):
    #     if j >= 0 and j < self.size: #check if the given i is within the board bounds
    #         if (i-1) >= 0: #check if its within the board bounds NORTH
    #             if self.check_For_Freeing((i-1), (j), board): #check for freed piece to the NORTH of the captured WEST/EAST piece
    #                 board[i-1][j] = current_player #frees currentPlayers Alligatus
    #         if (i+1) < self.size: #check if its within the board bounds SOUTH
    #             if self.check_For_Freeing((i+1), (j), board): #check for freed piece to the SOUTH of the captured WEST/EAST piece
    #                 board[i+1][j] = current_player #frees currentPlayers Alligatus

    # #check if piece on the given position has possibly been freed, returns true, if the piece has been freed, false if not (or there is no captured piece)
    # def check_For_Freeing(self, i, j, board):
    #     if board[i][j] == 2 or board[i][j] == -2: #check if the given piece is captured
    #         enemy_value = int(board[i][j]*-0.5)
    #         if (j-1 >= 0 and j+1 < self.size and board[i][j-1] == enemy_value
    #               and board[i][j+1] == enemy_value): #check if WEST/EAST pieces does capture the given piece
    #             return False
    #         elif (i-1 >= 0 and i+1 < self.size and board[i-1][j] == enemy_value
    #               and board[i+1][j] == enemy_value): #check if NORTH/SOUTH pieces does capture the given piece
    #             return False
    #         else: #if there is not a capturing pair of enemy pieces, return true and free the captured piece
    #             return True

    def terminal_test(self, state):
        super.__doc__
        return (state.board == 1).sum() < 2 or (state.board == -1).sum() < 2

    def utility(self, state, player):
        super.__doc__
        if player: # Player plays as white.
            return 0 if (state.board == 1).sum() == 1 else 1
        # Player plays as black.
        return 0 if (state.board == -1).sum() == 1 else 1