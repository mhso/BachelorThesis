"""
---------------------------------------------------------------------
latrunculi: Subclass of game. Implements game methods for latrunculi.
---------------------------------------------------------------------
"""
import numpy as np
from controller.game import Game
from model.state import State, Action
from enum import Enum

class PieceUtil:
    @staticmethod
    def piece_player_value(value):
        if value < 0: return 0
        elif value > 0: return 1
        else: return -1
    
    @staticmethod
    def player_color(value):
        if value > 0: return Field_Enum.WHITE
        return Field_Enum.BLACK

    @staticmethod
    def player_invers(value):
        return not value

    @staticmethod
    def piece_name(value):
        if value == -2: return Field_Enum.BLACK_TRAPPED
        elif value == -1: return Field_Enum.BLACK
        elif value == 1: return Field_Enum.WHITE
        elif value == 2: return Field_Enum.WHITE_TRAPPED
        else: return Field_Enum.NONE

    @staticmethod
    def piece_value(name):
        if name == Field_Enum.BLACK_TRAPPED: return -2
        elif name == Field_Enum.BLACK: return -1
        elif name == Field_Enum.WHITE: return 1
        elif name == Field_Enum.WHITE_TRAPPED: return 2
        else: return 0

    @staticmethod
    def norm_value(value):
        if value > 0: return 1
        elif value < 0: return -1
        else: return 0

    @staticmethod
    def trap_value(value):
        if value > 0: return 2
        elif value < 0: return -2
        else: return 0

    @staticmethod
    def invers_value(value):
        if value == -2: return -1
        elif value == -1: return -2
        elif value == 1: return 2
        elif value == 2: return 1
        else: return 0

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
                
                    self.append_list_if_valid(player_color, actionsList, (y, x), self.move_coords(Action_Move.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), self.move_coords(Action_Move.LEFT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), self.move_coords(Action_Move.RIGHT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), self.move_coords(Action_Move.DOWN, (y, x)))

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

        if move == Action_Move.UP or move == Action_Move.DOWN:
            return not self.valid_left_right(coords_to, player_color, opponent_color)

        elif move == Action_Move.LEFT or move == Action_Move.RIGHT:
            return not self.valid_up_down(coords_to, player_color, opponent_color)

        return True

    def valid_left_right(self, coords, player_color, opponent_color):

        left = self.move_coords(Action_Move.LEFT, coords)
        right = self.move_coords(Action_Move.RIGHT, coords)
        if self.is_empty_field(left) or self.is_empty_field(right) or not self.is_within_board(left) or not self.is_within_board(right):
            return True
        else:
            if self.is_within_board(left) and self.is_within_board(right) and self.field_value(left) == opponent_color and self.field_value(right) == opponent_color:
                
                left_left = self.move_coords(Action_Move.LEFT, left)
                right_right = self.move_coords(Action_Move.RIGHT, right)
                if self.is_within_board(left_left) and self.field_player(left_left) == player_color or self.is_within_board(right_right) and self.field_player(right_right) == player_color:
                    return True
                return False
            else:
                return True

    def valid_up_down(self, coords, player_color, opponent_color):
        
        up = self.move_coords(Action_Move.UP, coords)
        down = self.move_coords(Action_Move.DOWN, coords)
        up_up = self.move_coords(Action_Move.UP, up)
        down_down = self.move_coords(Action_Move.DOWN, down)

        if self.is_empty_field(up) or self.is_empty_field(down) or not self.is_within_board(up) or not self.is_within_board(down):
            return True
        else:           
            if self.is_within_board(up) and self.is_within_board(down) and self.field_value(up) == opponent_color and self.field_value(down) == opponent_color:

                up_up = self.move_coords(Action_Move.UP, up)
                down_down = self.move_coords(Action_Move.DOWN, down)
                if self.is_within_board(up_up) and self.field_player(up_up) == player_color or self.is_within_board(down_down) and self.field_player(down_down) == player_color:
                    return True
                return False
            else:
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
            return (y+1, x-1)
        elif direction == Action_Move.DOWN:
            return (y+1, x)
        elif direction == Action_Move.DOWN_RIGHT:
            return (y+1, x+1)
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

    def update_up_down(self, workboard, dest, current_player):
        y, x = dest

        for i in range(y, 0, -1):           
            if i > 2:
                this_c = i, x
                next_c1 = i-1, x
                next_c2 = i-2, x
                self.board_update(workboard, this_c, next_c1, next_c2, current_player)

        for i in range(y, self.board_no_of_rows):
            if i < self.board_no_of_rows-2:
                this_c = i, x
                next_c1 = i+1, x
                next_c2 = i+2, x
                self.board_update(workboard, this_c, next_c1, next_c2, current_player)
        return workboard
    
    def update_left_right(self, workboard, dest, current_player):
        y, x = dest

        for i in range(y, 0, -1):           
            if i > 2:
                this_c = y, i
                next_c1 = y, i-1
                next_c2 = y, i-2
                self.board_update(workboard, this_c, next_c1, next_c2, current_player)

        for i in range(y, self.board_no_of_cols):
            if i < self.board_no_of_cols-2:
                this_c = y, i
                next_c1 = y, i+1
                next_c2 = y, i+2
                self.board_update(workboard, this_c, next_c1, next_c2, current_player)
        return workboard

    def board_update(self, board, this_c, next_c1, next_c2, current_player):
        opponent_player = PieceUtil.player_invers(current_player)
        this_v = board[this_c]
        next_v1 = board[next_c1]
        next_v2 = board[next_c2]
        if PieceUtil.piece_player_value(this_v) == current_player and PieceUtil.piece_player_value(next_v1) == opponent_player  and PieceUtil.piece_player_value(next_v2) == current_player:
            v1 = PieceUtil.norm_value(this_v)
            v2 = PieceUtil.trap_value(next_v1)
            v3 = PieceUtil.norm_value(next_v2)
            print("Update: {} {} {}".format(v1, v2, v3))
            board[this_c] = v1
            board[next_c1] = v2
            board[next_c2] = v3

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
                
                newBoard = self.update_up_down(newBoard, dest, state.player)
                newBoard = self.update_left_right(newBoard, dest, state.player)

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

        return State(newBoard, (not state.player))

    def terminal_test(self, state):
        super.__doc__
        return (state.board == 1).sum() < 2 or (state.board == -1).sum() < 2

    def utility(self, state, player):
        super.__doc__
        if player: # Player plays as white.
            return 0 if (state.board == 1).sum() == 1 else 1
        # Player plays as black.
        return 0 if (state.board == -1).sum() == 1 else 1