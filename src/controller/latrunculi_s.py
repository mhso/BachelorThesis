"""
---------------------------------------------------------------------
latrunculi: Subclass of game. Implements game methods for latrunculi.
---------------------------------------------------------------------
"""
import numpy as np
from controller.game import Game
from model.state import State, Action
from enum import Enum

class FieldUtil:
    @staticmethod
    def piece_type(value):
        if value == -2:
            return FieldEnum.BLACK_TRAPPED
        elif value == -1:
            return FieldEnum.BLACK
        elif value == 1:
            return FieldEnum.WHITE
        elif value == 2:
            return FieldEnum.WHITE_TRAPPED
        else:
            return FieldEnum.NONE

    @staticmethod
    def piece_value(FieldEnum):
        if FieldEnum == FieldEnum.BLACK_TRAPPED:
            return -2
        elif FieldEnum == FieldEnum.BLACK:
            return -1
        elif FieldEnum == FieldEnum.WHITE:
            return 1
        elif FieldEnum == FieldEnum.WHITE_TRAPPED:
            return 2
        else: return 0

    @staticmethod
    def norm_value(value):
        if value > 0:
            return 1
        elif value < 0:
            return -1
        else:
            return 0

    @staticmethod
    def trap_value(value):
        if value > 0:
            return 2
        elif value < 0:
            return -2
        else:
            return 0

    @staticmethod
    def invers_state_value(value):
        if value == -2:
            return -1
        elif value == -1:
            return -2
        elif value == 1:
            return 2
        elif value == 2:
            return 1
        else:
            return 0

class PlayerUtil:
    @staticmethod
    def player_from_piece(value):
        if value < 0:
            return PlayerEnum.BLACK
        elif value > 0:
            return PlayerEnum.WHITE
        else:
            return PlayerEnum.NONE
    
    @staticmethod
    def player_color(value):
        if value == 0:
            return PlayerEnum.BLACK
        elif value == 1:
            return PlayerEnum.WHITE
        else:
            return PlayerEnum.NONE

    @staticmethod
    def player_to_value(playerEnum):
        if playerEnum == PlayerEnum.BLACK:
            return 0
        elif playerEnum == PlayerEnum.WHITE:
            return 1
        else:
            return -1
    
    @staticmethod
    def opponent_color(playerEnum):
        if playerEnum == PlayerEnum.BLACK:
            return PlayerEnum.WHITE
        else:
            return PlayerEnum.BLACK
    
    @staticmethod
    def player_from_non_trapped_piece(fieldEnum):
        if fieldEnum == FieldEnum.BLACK:
            return PlayerEnum.BLACK
        elif fieldEnum == FieldEnum.WHITE:
            return PlayerEnum.WHITE
        else:
            return PlayerEnum.NONE
    
    @staticmethod
    def player_from_trapped_piece(fieldEnum):
        if fieldEnum == FieldEnum.BLACK_TRAPPED:
            return PlayerEnum.BLACK
        elif fieldEnum == FieldEnum.WHITE_TRAPPED:
            return PlayerEnum.White
        else:
            return PlayerEnum.NONE
    
    @staticmethod
    def player_from_piece_type(fieldEnum):
        if fieldEnum == FieldEnum.BLACK_TRAPPED:
            return PlayerEnum.BLACK
        elif fieldEnum == FieldEnum.BLACK:
            return PlayerEnum.BLACK
        elif fieldEnum == FieldEnum.WHITE:
            return PlayerEnum.WHITE
        elif fieldEnum == FieldEnum.WHITE_TRAPPED:
            return PlayerEnum.WHITE
        else:
            return PlayerEnum.NONE


class MoveUtil:
    @staticmethod
    def move_coords(direction, coords):
        y, x = coords
        if direction == MoveEnum.UP_LEFT:
            return (y-1, x-1)
        elif direction == MoveEnum.UP:
            return (y-1, x)
        elif direction == MoveEnum.UP_RIGHT:
            return (y-1, x+1)

        elif direction == MoveEnum.LEFT:
            return (y, x-1)
        elif direction == MoveEnum.CENTER:
            return (y, x)
        elif direction == MoveEnum.RIGHT:
            return (y, x+1)

        elif direction == MoveEnum.DOWN_LEFT:
            return (y+1, x-1)
        elif direction == MoveEnum.DOWN:
            return (y+1, x)
        elif direction == MoveEnum.DOWN_RIGHT:
            return (y+1, x+1)
        return None

    @staticmethod
    def get_direction(coords_from, coords_to):
        y_from, x_from = coords_from
        y_to, x_to = coords_to
        if y_from-1 == y_to and x_from-1 == x_to:
            return MoveEnum.UP_LEFT
        elif y_from-1 == y_to and x_from == x_to:
            return MoveEnum.UP
        elif y_from-1 == y_to and x_from+1 == x_to:
            return MoveEnum.UP_RIGHT

        elif y_from == y_to and x_from-1 == x_to:
            return MoveEnum.LEFT
        elif y_from == y_to and x_from == x_to:
            return MoveEnum.CENTER
        elif y_from == y_to and x_from+1 == x_to:
            return MoveEnum.RIGHT
        
        elif y_from+1 == y_to and x_from-1 == x_to:
            return MoveEnum.DOWN_LEFT
        elif y_from+1 == y_to and x_from == x_to:
            return MoveEnum.DOWN
        elif y_from+1 == y_to and x_from+1 == x_to:
            return MoveEnum.DOWN_RIGHT
        return None

class MoveEnum(Enum):
    UP_LEFT = 1
    UP = 2
    UP_RIGHT = 3
    LEFT = 4
    CENTER = 5
    RIGHT = 6
    DOWN_LEFT = 7
    DOWN = 8
    DOWN_RIGHT = 9

class FieldEnum(Enum):
    BLACK_TRAPPED = -2
    BLACK = -1
    NONE = 0
    WHITE = 1
    WHITE_TRAPPED = 2

class PlayerEnum(Enum):
    BLACK = 10
    WHITE = 20
    NONE = 30

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

        player_color = PlayerUtil.player_color(state.player)

        actionsList = []

        self.board = state.board
        for y in range(self.board_no_of_rows):
            for x in range(self.board_no_of_cols):
                if PlayerUtil.player_from_piece(self.board[y, x]) == player_color:
                
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.LEFT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.RIGHT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.DOWN, (y, x)))

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
        move = MoveUtil.get_direction(coords_from, coords_to)
        opponent_color = PlayerUtil.opponent_color(player_color)

        if move == MoveEnum.UP or move == MoveEnum.DOWN:
            return not self.valid_coords(MoveEnum.LEFT, MoveEnum.RIGHT, coords_to, player_color, opponent_color)

        elif move == MoveEnum.LEFT or move == MoveEnum.RIGHT:
            return not self.valid_coords(MoveEnum.UP, MoveEnum.DOWN, coords_to, player_color, opponent_color)

        return True

    def valid_coords(self, direction1, direction2, coords, player_color, opponent_color):
        coord1_c = MoveUtil.move_coords(direction1, coords)
        coord2_c = MoveUtil.move_coords(direction2, coords)

        if (self.is_empty_field(coord1_c) or not self.is_within_board(coord1_c)
            or self.is_empty_field(coord2_c) or not self.is_within_board(coord2_c)):
            return True
        else:
            coord1_v = self.board[coord1_c]
            coord2_v = self.board[coord2_c]
            if (self.is_within_board(coord1_c) and self.is_within_board(coord2_c)
                and PlayerUtil.player_from_non_trapped_piece(FieldUtil.piece_type(coord1_v)) == opponent_color
                and PlayerUtil.player_from_non_trapped_piece(FieldUtil.piece_type(coord2_v)) == opponent_color):
                
                coord1_c = MoveUtil.move_coords(direction1, coords)
                coord2_c = MoveUtil.move_coords(direction2, coords)
                coord1_v = self.board[coord1_c]
                coord2_v = self.board[coord2_c]
                if (self.is_within_board(coord1_c) and self.is_within_board(coord2_c)
                    and PlayerUtil.player_from_piece_type(FieldUtil.piece_type(coord1_v)) == player_color
                    and PlayerUtil.player_from_piece_type(FieldUtil.piece_type(coord2_v)) == player_color):
                    return True
                return False
            else:
                return True

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
        opponent_player = PlayerUtil.opponent_color(current_player)
        this_v = board[this_c]
        next_v1 = board[next_c1]
        next_v2 = board[next_c2]
        if (PlayerUtil.player_from_piece_type(FieldUtil.piece_type(this_v)) == current_player
            and PlayerUtil.player_from_piece_type(FieldUtil.piece_type(next_v1)) == opponent_player
            and PlayerUtil.player_from_piece_type(FieldUtil.piece_type(next_v2)) == current_player):

            v1 = FieldUtil.norm_value(this_v)
            v2 = FieldUtil.trap_value(next_v1)
            v3 = FieldUtil.norm_value(next_v2)
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
                
                current_player = PlayerUtil.player_color(state.player)

                newBoard = self.update_up_down(newBoard, dest, current_player)
                newBoard = self.update_left_right(newBoard, dest, current_player)

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