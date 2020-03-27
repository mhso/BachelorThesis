"""
---------------------------------------------------------------------
latrunculi: Subclass of game. Implements game methods for latrunculi.
---------------------------------------------------------------------
"""
import numpy as np
from enum import Enum

class PieceUtil:
    @staticmethod
    def player_value(value):
        if value < 0: return 0
        elif value > 0: return 1
        else: return -1
    
    @staticmethod
    def player_color(value):
        if value > 0: return Field_Enum.WHITE
        return Field_Enum.BLACK

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

class State:
    board = []
    player = True

    def __init__(self, board, player):
        self.board = board
        self.player = player

    def __str__(self):
        player = "White" if self.player else "Black"
        white_pieces = (self.board == 1).sum()
        black_pieces = (self.board == -1).sum()
        return "[State: \nPlayer turn = {}\nWhite pieces = {}\nBlack pieces = {}\nBoard =\n{}\n]".format(
            player, white_pieces, black_pieces, self.board)

    def stringify(self):
        return ("1" if self.player else "0") + ("".join([str(p) for p in self.board.ravel()]))

class Action:
    source = 0, 0
    dest = 0, 0

    def __init__(self, source, dest):
        self.source = source
        self.dest = dest

    def __eq__(self, other):
        return self.source == other.source and self.dest == other.dest

    def numeric(self):
        """
        Return unique numeric ID of Action.
        Used in MCTS
        """
        x1, y1 = self.source
        x2, y2 = self.dest
        return int(str(x1)+str(y1)+str(x2)+str(y2))

    def __str__(self):
        return "[Action: source({}), dest({})]".format(self.source, self.dest)


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

class Latrunculi_s():
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
        self.board = board

    def __init__(self, size, start_seed=None):
        self.size = size
        self.populate_board(start_seed)
        self.print_board()
    
    def print_board(self):
        print("--- BOARD ---")
        print(self.board)

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
        

        # if move == Action_Move.UP:
        #     return not self.valid_left_right(coords_to, player_color, opponent_color)

        # elif move == Action_Move.LEFT:
        #     return not self.valid_up_down(coords_to, player_color, opponent_color)

        if move == Action_Move.RIGHT:
            return not self.valid_up_down(coords_to, player_color, opponent_color)

        # elif move == Action_Move.DOWN:
        #     return not self.valid_left_right(coords_to, player_color, opponent_color)

        return True

    def valid_left_right(self, coords, player_color, opponent_color):

        left = self.move_coords(Action_Move.LEFT, coords)
        right = self.move_coords(Action_Move.RIGHT, coords)
        if self.is_empty_field(left) or self.is_empty_field(right) or not self.is_within_board(left) or not self.is_within_board(right):
            # if coords == (3, 5): print("{} valid_left_right empty field or not within board".format(coords))
            return True
        else:
            if self.is_within_board(left) and self.is_within_board(right) and self.field_value(left) == opponent_color and self.field_value(right) == opponent_color:
                
                left_left = self.move_coords(Action_Move.LEFT, left)
                right_right = self.move_coords(Action_Move.RIGHT, right)
                if self.is_within_board(left_left) and self.field_player(left_left) == player_color or self.is_within_board(right_right) and self.field_player(right_right) == player_color:
                    return True
                #if coords == (3, 5): print("{} valid_left_right within board and not opponent colors".format(coords))
                return False
            else:
                #if coords == (3, 5): print("{} valid_left_right not within board or not opponent colors".format(coords))
                return True

    def valid_up_down(self, coords, player_color, opponent_color):
        
        up = self.move_coords(Action_Move.UP, coords)
        down = self.move_coords(Action_Move.DOWN, coords)
        up_up = self.move_coords(Action_Move.UP, up)
        down_down = self.move_coords(Action_Move.DOWN, down)

        if self.is_empty_field(up) or self.is_empty_field(down) or not self.is_within_board(up) or not self.is_within_board(down):
            # if coords == (3, 5): print("{} valid_up_down empty field or not within board".format(coords))
            return True
        else:           
            if self.is_within_board(up) and self.is_within_board(down) and self.field_value(up) == opponent_color and self.field_value(down) == opponent_color:

                up_up = self.move_coords(Action_Move.UP, up)
                down_down = self.move_coords(Action_Move.DOWN, down)
                if self.is_within_board(up_up) and self.field_player(up_up) == player_color or self.is_within_board(down_down) and self.field_player(down_down) == player_color:
                    print("{} valid_up_down".format(coords))
                    print("{} up".format(up))
                    print("{} down".format(down))
                    print("{} up_up".format(up_up))
                    print("{} down_down".format(down_down))
                    return True
                # if coords == (3, 5): print("{} valid_up_down within board and not opponent colors".format(coords))
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

    def field_trapped_color(self, value):
        if value == Field_Enum.BLACK_TRAPPED or value == Field_Enum.BLACK:
            return Field_Enum.BLACK_TRAPPED
        elif value == Field_Enum.WHITE_TRAPPED  or value == Field_Enum.WHITE:
            return Field_Enum.WHITE_TRAPPED
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

    def update_up_down(self, dest):
        self.print_board()
        newBoard = np.copy(self.board)
        newBoard[(5, 2)] = 0
        newBoard[dest] = -1
        self.board = newBoard
        y, x = dest
        current_player = 0
        opponent_player = 1

        for i in range(y, 0, -1):           
            if i > 2:
                this_c = i, x
                next_c1 = i-1, x
                next_c2 = i-2, x
                self.board_update(newBoard, this_c, next_c1, next_c2, current_player, opponent_player)

        print("\n")
        self.print_board()
        print("\n")
        for i in range(y, self.board_no_of_rows):
            if i < self.board_no_of_rows-2:
                this_c = i, x
                next_c1 = i+1, x
                next_c2 = i+2, x
                self.board_update(newBoard, this_c, next_c1, next_c2, current_player, opponent_player)
                

        self.board = newBoard
        self.print_board()
        return "done"

    def board_update(self, board, this_c, next_c1, next_c2, current_player, opponent_player):
        this_v = board[this_c]
        next_v1 = board[next_c1]
        next_v2 = board[next_c2]
        if PieceUtil.player_value(this_v) == current_player and PieceUtil.player_value(next_v1) == opponent_player  and PieceUtil.player_value(next_v2) == current_player:
            v1 = PieceUtil.norm_value(this_v)
            v2 = PieceUtil.trap_value(next_v1)
            v3 = PieceUtil.norm_value(next_v2)
            print("Update: {} {} {}".format(v1, v2, v3))
            board[this_c] = v1
            board[next_c1] = v2
            board[next_c2] = v3

lat_s = Latrunculi_s(8, 422)


############ TESTS ############

print("piece_color: {}".format(lat_s.piece_color(-2)))
print("piece_color: {}".format(lat_s.piece_color(-1)))
print("piece_color: {}".format(lat_s.piece_color(0)))
print("piece_color: {}".format(lat_s.piece_color(1)))
print("piece_color: {}".format(lat_s.piece_color(2)))
print("\n")
print("oppenent_player_color: {}".format(lat_s.oppenent_player_color(Field_Enum.BLACK)))
print("oppenent_player_color: {}".format(lat_s.oppenent_player_color(Field_Enum.WHITE)))
print("\n")
print("player_color: {}".format(lat_s.player_color(0)))
print("player_color: {}".format(lat_s.player_color(1)))
print("player_color: {}".format(lat_s.player_color(2)))
print("\n")
coords_from = (5, 2)
print("player_color: {}".format(lat_s.get_direction(coords_from, (4, 1))))
print("player_color: {}".format(lat_s.get_direction(coords_from, (4, 2))))
print("player_color: {}".format(lat_s.get_direction(coords_from, (4, 3))))

print("player_color: {}".format(lat_s.get_direction(coords_from, (5, 1))))
print("player_color: {}".format(lat_s.get_direction(coords_from, (5, 2))))
print("player_color: {}".format(lat_s.get_direction(coords_from, (5, 3))))

print("player_color: {}".format(lat_s.get_direction(coords_from, (6, 1))))
print("player_color: {}".format(lat_s.get_direction(coords_from, (6, 2))))
print("player_color: {}".format(lat_s.get_direction(coords_from, (6, 3))))
print("\n")
coords_from = (5, 2)
print("player_color: {}".format(lat_s.move_coords(Action_Move.UP_LEFT, coords_from)))
print("player_color: {}".format(lat_s.move_coords(Action_Move.UP, coords_from)))
print("player_color: {}".format(lat_s.move_coords(Action_Move.UP_RIGHT, coords_from)))

print("player_color: {}".format(lat_s.move_coords(Action_Move.LEFT, coords_from)))
print("player_color: {}".format(lat_s.move_coords(Action_Move.CENTER, coords_from)))
print("player_color: {}".format(lat_s.move_coords(Action_Move.RIGHT, coords_from)))

print("player_color: {}".format(lat_s.move_coords(Action_Move.DOWN_LEFT, coords_from)))
print("player_color: {}".format(lat_s.move_coords(Action_Move.DOWN, coords_from)))
print("player_color: {}".format(lat_s.move_coords(Action_Move.DOWN_RIGHT, coords_from)))

print("\n")
print("player_color: {}".format(lat_s.field_player_color(Field_Enum.WHITE)))
print("player_color: {}".format(lat_s.field_player_color(Field_Enum.WHITE_TRAPPED)))
print("player_color: {}".format(lat_s.field_player_color(Field_Enum.BLACK)))
print("player_color: {}".format(lat_s.field_player_color(Field_Enum.BLACK_TRAPPED)))
print("player_color: {}".format(lat_s.field_player_color(Field_Enum.NONE)))

print("\n")
coords_from = (5, 2)
print("is_suicide_move UP: {}".format(lat_s.is_suicide_move(coords_from, lat_s.move_coords(Action_Move.UP, coords_from), Field_Enum.BLACK)))
print("is_suicide_move LEFT: {}".format(lat_s.is_suicide_move(coords_from, lat_s.move_coords(Action_Move.LEFT, coords_from), Field_Enum.BLACK)))
print("is_suicide_move RIGHT: {}".format(lat_s.is_suicide_move(coords_from, lat_s.move_coords(Action_Move.RIGHT, coords_from), Field_Enum.BLACK)))
print("is_suicide_move DOWN: {}".format(lat_s.is_suicide_move(coords_from, lat_s.move_coords(Action_Move.DOWN, coords_from), Field_Enum.BLACK)))

print("\n")
coords_from = (5, 3)
print("update_up_down: {}".format(lat_s.update_up_down(coords_from)))
