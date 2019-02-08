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
            return PlayerEnum.WHITE
        else:
            return PlayerEnum.NONE
    
    @staticmethod
    def opponent_from_trapped_piece(fieldEnum):
        if fieldEnum == FieldEnum.BLACK_TRAPPED:
            return PlayerEnum.WHITE
        elif fieldEnum == FieldEnum.WHITE_TRAPPED:
            return PlayerEnum.BLACK
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

        it = np.nditer(state.board, flags=["multi_index"])
        while not it.finished:
            (y, x) = it.multi_index
            if PlayerUtil.player_from_non_trapped_piece(FieldUtil.piece_type(self.board[y, x])) == player_color:
                
                y_max = self.board_no_of_rows-1
                x_max = self.board_no_of_cols-1

                if y == 0 and x == 0:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.RIGHT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.DOWN, (y, x)))
                elif y == 0 and x == x_max:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.LEFT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.DOWN, (y, x)))
                elif y == y_max and x == x_max:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.LEFT, (y, x)))
                elif y == y_max and x == 0:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.RIGHT, (y, x)))
                elif y == 0 and x > 0 and x < x_max:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.LEFT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.RIGHT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.DOWN, (y, x)))
                elif y == y_max and x > 0 and x < x_max:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.LEFT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.RIGHT, (y, x)))
                elif y > 0 and y < y_max and x == 0:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.RIGHT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.DOWN, (y, x)))
                elif y > 0 and y < y_max and x == x_max:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.LEFT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.DOWN, (y, x)))
                else:
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.UP, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.LEFT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.RIGHT, (y, x)))
                    self.append_list_if_valid(player_color, actionsList, (y, x), MoveUtil.move_coords(MoveEnum.DOWN, (y, x)))


            elif PlayerUtil.opponent_from_trapped_piece(FieldUtil.piece_type(self.board[y, x])) == player_color: # if the current piece, is the opponents captured piece
                actionsList.append(Action((y, x), (y, x))) # action to remove an opponents captured piece
            it.iternext()

        if actionsList == []:
            actionsList.append(None)
        return actionsList

    def is_within_board(self, coords):
        y, x = coords
        return 0 <= x and x < self.board_no_of_rows and 0 <= y and y < self.board_no_of_rows
    
    def is_empty_field(self, coords):
        return self.is_within_board(coords) and self.board[coords] == 0
    
    def append_list_if_valid(self, player_color, alist, coords_from, coords_to):
        if not self.is_suicide_move(coords_from, coords_to, player_color):
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


    # def result(self, state, action):
    #     super.__doc__
    #     if action is None:
    #         return State(state.board, (not state.player))
    #     source = action.source
    #     dest = action.dest
    #     current_player = -1 #Black
    #     enemy_player = 1
    #     if state.player:
    #         current_player = 1 #White
    #         enemy_player = -1

    #     newBoard = np.copy(state.board) #newBoard is the one that will be returned
        
    #     if state.board[source] == current_player: #if source is a piece owned by the current player
    #         if not source == dest: #check if source and dest are different 
    #             illegal_action = True
    #             for ac in self.actions(state):
    #                 if ac.source == source and ac.dest == dest:
    #                     illegal_action = False
                
    #             if illegal_action:
    #                 raise Exception("you have attempted an illegal move...")
                
    #             newBoard[source] = 0
    #             newBoard[dest] = current_player
                
    #             current_player = PlayerUtil.player_color(state.player)

    #             newBoard = self.update_up_down(newBoard, dest, current_player)
    #             newBoard = self.update_left_right(newBoard, dest, current_player)

    #             print("Lets move the piece")

    #         else:
    #             raise Exception("you attempted to move your piece, to the square where the piece started")
    #     elif state.board[source] == (enemy_player*2): #if source is an opponents captured piece
    #         if source == dest: #if source and dest is equal, remove opponents captured piece
    #             newBoard[source] = 0 #removed captured piece
    #         else:
    #             raise Exception("you have attempted to move an opponents captured piece...")
    #     else: #If none of the above, illegal move...
    #         raise Exception("you have attempted to move a piece that you do not own...")

    #     return State(newBoard, (not state.player))

    # def terminal_test(self, state):
    #     super.__doc__
    #     return (state.board == 1).sum() < 2 or (state.board == -1).sum() < 2

    # def utility(self, state, player):
    #     super.__doc__
    #     if player: # Player plays as white.
    #         return 0 if (state.board == 1).sum() == 1 else 1
    #     # Player plays as black.
    #     return 0 if (state.board == -1).sum() == 1 else 1

    def result(self, state, action):
        super.__doc__
        if action is None:
            return State(state.board, (not state.player))
        source = action.source
        dest = action.dest
        current_player = 0
        enemy_player = 0
        if state.player:
            current_player = 1 #White
            enemy_player = -1
        else:
            current_player = -1 #Black
            enemy_player = 1
        newBoard = np.copy(state.board) #newBoard is the one that will be returned
        if state.board[source[0]][source[1]] == current_player: #if source is a piece owned by the current player
            if source[0] != dest[0] or source[1] != dest[1]: #check if source and dest are different
                i = dest[0]
                j = dest[1]
                newBoard[i][j] = current_player #moves piece to destination (dest)
                newBoard[source[0]][source[1]] = 0 #removes piece from source
                workBoard = np.copy(newBoard) #workBoard is the one that is checked during the method

                #check if the move frees an opponents captured piece
                self.check_For_Freeing_Due_To_Move(source[0], source[1], newBoard, enemy_player)

                #check for suicide moves
                if (i-1) >= 0 and (i+1) < self.size: #check if possible suicide move is within board bounds NORTH/SOUTH
                    if workBoard[i-1][j] == enemy_player and workBoard[i+1][j] == enemy_player: #check for suicide move NORTH/SOUTH
                        #NORTH
                        if (i-2) >= 0: #check if suicide move capture, is within board bounds NORTH
                            if workBoard[i-2][j] == current_player: #check for suicide move capture NORTH
                                newBoard[i-1][j] = enemy_player*2 #captures the oppenents piece NORTH
                                self.freed_Check_West_East_of_Piece((i-1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                        #SOUTH
                        if (i+2) < self.size: #check if suicide move capture, is within board bounds SOUTH
                            if workBoard[i+2][j] == current_player: #check for suicide move capture SOUTH
                                newBoard[i+1][j] = enemy_player*2 #captures the oppenents piece SOUTH
                                #check for freeing of another piece
                                self.freed_Check_West_East_of_Piece((i+1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece

                if (j-1) >= 0 and (j+1) < self.size: #check if possible suicide move is within board bounds WEST/EAST
                    if workBoard[i][j-1] == enemy_player and workBoard[i][j+1] == enemy_player: #check for suicide move WEST/EAST
                        #WEST
                        if (j-2) >= 0: #check if suicide move capture, is within board bounds WEST
                            if workBoard[i][j-2] == current_player: #check for suicide move capture WEST
                                newBoard[i][j-1] = enemy_player*2 #captures the oppenents piece WEST
                                self.freed_Check_North_South_of_Piece(i, (j-1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                        #EAST
                        if (j+2) < self.size: #check if suicide move capture, is within board bounds EAST
                            if workBoard[i][j+2] == current_player: #check for suicide move capture EAST
                                newBoard[i][j+1] = enemy_player*2 #captures the oppenents piece EAST
                                self.freed_Check_North_South_of_Piece(i, (j+1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece

                #check for regular capture of enemies
                #NORTH
                if (i-2) >= 0: #check if possible regular capture is within board bounds NORTH
                    if workBoard[i-1][j] == enemy_player and workBoard[i-2][j] == current_player: #check for regular capture NORTH
                        newBoard[i-1][j] = enemy_player*2 #capture the opponents piece NORTH
                        self.freed_Check_West_East_of_Piece((i-1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                #SOUTH
                if (i+2) < self.size: #check if possible regular capture is within board bounds SOUTH
                    if workBoard[i+1][j] == enemy_player and workBoard[i+2][j] == current_player: #check for regular capture SOUTH
                        newBoard[i+1][j] = enemy_player*2 #capture the opponents piece SOUTH
                        self.freed_Check_West_East_of_Piece((i+1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                #WEST
                if (j-2) >= 0: #check if possible regular capture is within board bounds WEST
                    if workBoard[i][j-1] == enemy_player and workBoard[i][j-2] == current_player: #check for regular capture WEST
                        newBoard[i][j-1] = enemy_player*2 #capture the opponents piece WEST
                        self.freed_Check_North_South_of_Piece(i, (j-1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                #EAST
                if (j+2) < self.size: #check if possible regular capture is within board bounds EAST
                    if workBoard[i][j+1] == enemy_player and workBoard[i][j+2] == current_player: #check for regular capture EAST
                        newBoard[i][j+1] = enemy_player*2 #capture the opponents piece EAST
                        self.freed_Check_North_South_of_Piece(i, (j+1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
            else:
                raise Exception("you attempted to move your piece, to the square where the piece started")
        elif state.board[source[0]][source[1]] == (enemy_player*2): #if source is an opponents captured piece
            if source[0] == dest[0] and source[1] == dest[1]: #if source and dest is equal, remove opponents captured piece
                newBoard[source[0]][source[1]] = 0 #removed captured piece
            else:
                raise Exception("you have attempted to move an opponents captured piece...")
        else: #If none of the above, illegal move...
            raise Exception("you have attempted to move a piece that you do not own...")
        return State(newBoard, (not state.player))

    #checks whether moving a piece from its source, causes an enemys piece to be freed
    def check_For_Freeing_Due_To_Move(self, i, j, board, enemy):
        if (i-1) >= 0: #check that we are within board bounds
            if self.check_For_Freeing((i-1), j, board): #checks piece NORTH of source
                board[i-1][j] = enemy #frees piece
        if (i+1) < self.size: #check that we are within board bounds
            if self.check_For_Freeing((i+1), j, board): #checks piece SOUTH of source
                board[i+1][j] = enemy #frees piece
        if (j-1) >= 0: #check that we are within board bounds
            if self.check_For_Freeing(i, (j-1), board): #checks piece WEST of source
                board[i][j-1] = enemy #frees piece
        if (j+1) < self.size: #check that we are within board bounds
            if self.check_For_Freeing(i, (j+1), board): #checks piece EAST of source
                board[i][j+1] = enemy #frees piece

    #check for freed pieces to the WEST/EAST of the given piece
    def freed_Check_West_East_of_Piece(self, i, j, board, current_player):
        if i >= 0 and i < self.size: #check if the given i is within the board bounds
            if (j-1) >= 0: #check if its within the board bounds WEST
                if self.check_For_Freeing((i), (j-1), board): #check for freed piece to the WEST of the captured NORTH/SOUTH piece
                    board[i][j-1] = current_player #frees currentPlayers Alligatus
            if (j+1) < self.size: #check if its within the board bounds EAST
                if self.check_For_Freeing((i), (j+1), board): #check for freed piece to the EAST of the captured NORTH/SOUTH piece
                    board[i][j+1] = current_player #frees currentPlayers Alligatus
    
    #check for freed pieces to the NORTH/SOUTH of the given piece
    def freed_Check_North_South_of_Piece(self, i, j, board, current_player):
        if j >= 0 and j < self.size: #check if the given i is within the board bounds
            if (i-1) >= 0: #check if its within the board bounds NORTH
                if self.check_For_Freeing((i-1), (j), board): #check for freed piece to the NORTH of the captured WEST/EAST piece
                    board[i-1][j] = current_player #frees currentPlayers Alligatus
            if (i+1) < self.size: #check if its within the board bounds SOUTH
                if self.check_For_Freeing((i+1), (j), board): #check for freed piece to the SOUTH of the captured WEST/EAST piece
                    board[i+1][j] = current_player #frees currentPlayers Alligatus

    #check if piece on the given position has possibly been freed, returns true, if the piece has been freed, false if not (or there is no captured piece)
    def check_For_Freeing(self, i, j, board):
        if board[i][j] == 2 or board[i][j] == -2: #check if the given piece is captured
            enemy_value = int(board[i][j]*-0.5)
            if (j-1 >= 0 and j+1 < self.size and board[i][j-1] == enemy_value
                  and board[i][j+1] == enemy_value): #check if WEST/EAST pieces does capture the given piece
                return False
            elif (i-1 >= 0 and i+1 < self.size and board[i-1][j] == enemy_value
                  and board[i+1][j] == enemy_value): #check if NORTH/SOUTH pieces does capture the given piece
                return False
            else: #if there is not a capturing pair of enemy pieces, return true and free the captured piece
                return True

    def terminal_test(self, state):
        super.__doc__
        return (state.board == 1).sum() < 2 or (state.board == -1).sum() < 2

    def utility(self, state, player):
        super.__doc__
        if player: # Player plays as white.
            return 0 if (state.board == 1).sum() == 1 else 1
        # Player plays as black.
        return 0 if (state.board == -1).sum() == 1 else 1
        