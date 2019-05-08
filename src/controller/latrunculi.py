"""
---------------------------------------------------------------------
latrunculi: Subclass of game. Implements game methods for latrunculi.
---------------------------------------------------------------------
"""
import numpy as np
from numba import jit
from controller.game import Game
from model.state import State, Action

#i needed this quick, but there might be a library method for this, just could not find it
#this method helps construct a stop value for the range used in jump calculations, it makes any negative integer into -1
#which should let the range run to 0 inclusive, which is what we want, because the stop value is exclusive
@jit(nopython=True)
def convert_to_positive_int(x):
    if x < 0:
        return -1
    else:
        return x

# checks the squares north or south of a players piece, and acts accordingly
@jit(nopython=True)    
def check_North_Or_South_From_Player_Piece(size, i, j, direction, player, board): #perhaps just pass along the board????
    actionsList = []
    if board[i + direction][j] == 0: #check for NORTH/SOUTH square being empty
        if (j - 1) >= 0 and (j + 1) < size: #check for whether insta-capture is possible or if we are too close to edge of the board
            actionsList.extend(check_for_capture_and_suicide_west_or_east_of_given_piece(size, i, j, (i+direction), j, player, board))
        else:  #if there is no chance for insta capture, create action to empty square
            actionsList.append((i, j, i+direction, j))
    else: # if the north/south square contains a piece (either 1, 2, -1, -2), check for jumps
        for x in range(i + (2*direction), (convert_to_positive_int(size * direction)), 2*direction): #Jump-loop
            if x >= 0 and x < size: #check that x squares north/south is within the bounds of the board 
                if board[x + (-1*direction)][j] != 0: #check if there is a piece on the odd number square north/south... #this is a double check for the first jump, might want to optimize it...
                    if board[x][j] == 0: #checks for the even number square north/south being empty, if the square before was occupied
                        #check for capture/suicide in all directions of the jump destination
                        jumpActions = check_for_capture_and_suicide_all_directions_of_given_piece(size, i, j, x, j, player, board)
                        if len(jumpActions) != 0:
                            actionsList.extend(jumpActions)
                        else:
                            break #this jump results in capture, which breaks the jump chain
                    else:
                        break #jump chain is broken
                else:
                    break #jump chain is broken
            else:
                break #break if outside of board bounds
    return actionsList

# checks the squares west or east of a players piece, and acts accordingly
@jit(nopython=True)
def check_West_Or_East_From_Player_Piece(size, i, j, direction, player, board):
    actionsList = []
    if board[i][j + direction] == 0: #check for WEST/EAST square being empty
        if (i - 1) >= 0 and (i + 1) < size: #check for whether insta-capture is possible or if we are too close to edge of the board
            actionsList.extend(check_for_capture_and_suicide_north_or_south_of_given_piece(size, i, j, i, (j+direction), player, board))
        else:  #if there is no chance for insta capture, create action to empty square
            actionsList.append((i, j, i, j+direction))
    else: # if the WEST/EAST square contains a piece (either 1, 2, -1, -2), check for jumps
        for x in range(j + (2*direction), (convert_to_positive_int((size*direction))), (2*direction)): #Jump-loop
            if x >= 0 and x < size: #check that x squares WEST/EAST is within the bounds of the board
                if board[i][(x + (-1*direction))] != 0: #check if there is a piece on the odd number square WEST/EAST... #this is a double check for the first jump, might want to optimize it...
                    if board[i][x] == 0: #checks for the even number square WEST/EAST being empty, if the square before was occupied
                        #check for capture/suicide in all directions of the jump destination
                        jumpActions = check_for_capture_and_suicide_all_directions_of_given_piece(size, i, j, i, x, player, board)
                        if len(jumpActions) != 0:
                            actionsList.extend(jumpActions)
                        else:
                            break #this jump results in capture, which breaks the jump chain
                    else:
                        break #jump chain is broken
                else:
                    break #jump chain is broken
            else:
                break #break if outside of board bounds
    return actionsList

@jit(nopython=True)
def check_for_capture_and_suicide_all_directions_of_given_piece(size, iOrigin, jOrigin, iDest, jDest, player, board):
    action_list = []
    boolWE = check_for_capture_and_suicide_west_or_east_of_given_piece_bool(size, iOrigin, jOrigin, iDest, jDest, player, board) #check for insta-capture WEST/EAST
    boolNS = check_for_capture_and_suicide_north_or_south_of_given_piece_bool(size, iOrigin, jOrigin, iDest, jDest, player, board) #check for insta-capture NORTH/SOUTH

    if boolWE and boolNS: #checks whether any insta capture was found, false means that an insta-capture exists on this square
        action_list.append((iOrigin, jOrigin, iDest, jDest)) #if the move is legal, create action

    return action_list #return the actions_list which is empty if no legal move was found.

@jit(nopython=True)
#returns false if there is an insta-capture and no suicide option, true if there is no insta-capture WE
def check_for_capture_and_suicide_west_or_east_of_given_piece_bool(size, iOrigin, jOrigin, iDest, jDest, player, board):
    enemy_player = -1*player
    if (jDest - 1) >= 0 and (jDest + 1) < size: #check if there is room for a possible insta-capture WEST/EAST
        if board[iDest][jDest + 1] == enemy_player and board[iDest][jDest - 1] == enemy_player: #check for insta capture
            if (jDest - 2) >= 0 and board[iDest][jDest - 2] == player and (jDest - 2) != jOrigin: #check for possible suicide action to the west
                return True
            elif (jDest + 2) < size and board[iDest][jDest + 2] == player and (jDest + 2) != jOrigin: #check for possible suicide action to the east
                return True
            else:
                return False
    return True

@jit(nopython=True)
#returns false if there is an insta-capture and no suicide option, true if there is no insta-capture NS
def check_for_capture_and_suicide_north_or_south_of_given_piece_bool(size, iOrigin, jOrigin, iDest, jDest, player, board):
    enemy_player = -1*player
    if (iDest - 1) >= 0 and (iDest + 1) < size: #check if there is room for a possible insta-capture NORTH/SOUTH
        if board[iDest + 1][jDest] == enemy_player and board[iDest - 1][jDest] == enemy_player: #check for insta capture
            if (iDest - 2) >= 0 and board[iDest - 2][jDest] == player and (iDest - 2) != iOrigin: #check for possible suicide action to the north
                return True
            elif (iDest + 2) < size and board[iDest + 2][jDest] == player and (iDest + 2) != iOrigin: #check for possible suicide action to the south
                return True
            else:
                return False
    return True

@jit(nopython=True)
def check_for_capture_and_suicide_west_or_east_of_given_piece(size, iOrigin, jOrigin, iDest, jDest, player, board):
    enemy_player = -1*player
    action_list = []
    if (jDest - 1) >= 0 and (jDest + 1) < size: #check if there is room for a possible insta-capture WEST/EAST
        if board[iDest][jDest + 1] == enemy_player and board[iDest][jDest - 1] == enemy_player: #check for insta capture
            if (jDest - 2) >= 0 and board[iDest][jDest - 2] == player and (jDest - 2) != jOrigin: #check for possible suicide action to the west
                    action_list.append((iOrigin, jOrigin, iDest, jDest))
            elif (jDest + 2) < size and board[iDest][jDest + 2] == player and (jDest + 2) != jOrigin: #check for possible suicide action to the east
                    action_list.append((iOrigin, jOrigin, iDest, jDest))
        else: #if there is no insta capture on this square, create action
            action_list.append((iOrigin, jOrigin, iDest, jDest))
    else: #if there is no room for an insta capture on this square, create action
            action_list.append((iOrigin, jOrigin, iDest, jDest))
    return action_list

@jit(nopython=True)
def check_for_capture_and_suicide_north_or_south_of_given_piece(size, iOrigin, jOrigin, iDest, jDest, player, board):
    enemy_player = -1*player
    action_list = []
    if (iDest - 1) >= 0 and (iDest + 1) < size: #check if there is room for a possible insta-capture NORTH/SOUTH
        if board[iDest + 1][jDest] == enemy_player and board[iDest - 1][jDest] == enemy_player: #check for insta capture
            if (iDest - 2) >= 0 and board[iDest - 2][jDest] == player and (iDest - 2) != iOrigin: #check for possible suicide action to the north
                    action_list.append((iOrigin, jOrigin, iDest, jDest))
            elif (iDest + 2) < size and board[iDest + 2][jDest] == player and (iDest + 2) != iOrigin: #check for possible suicide action to the south
                    action_list.append((iOrigin, jOrigin, iDest, jDest))
        else: #if there is no insta capture on this square, create action
            action_list.append((iOrigin, jOrigin, iDest, jDest))
    else: #if there is no room for an insta capture on this square, create action
        action_list.append((iOrigin, jOrigin, iDest, jDest))
    return action_list

#checks whether moving a piece from its source, causes an enemys piece to be freed
@jit(nopython=True)
def check_For_Freeing_Due_To_Move(size, i, j, board, enemy):
    if (i-1) >= 0: #check that we are within board bounds
        if check_For_Freeing(size, (i-1), j, board): #checks piece NORTH of source
            board[i-1][j] = enemy #frees piece
    if (i+1) < size: #check that we are within board bounds
        if check_For_Freeing(size, (i+1), j, board): #checks piece SOUTH of source
            board[i+1][j] = enemy #frees piece
    if (j-1) >= 0: #check that we are within board bounds
        if check_For_Freeing(size, i, (j-1), board): #checks piece WEST of source
            board[i][j-1] = enemy #frees piece
    if (j+1) < size: #check that we are within board bounds
        if check_For_Freeing(size, i, (j+1), board): #checks piece EAST of source
            board[i][j+1] = enemy #frees piece

#check for freed pieces to the WEST/EAST of the given piece
@jit(nopython=True)
def freed_Check_West_East_of_Piece(size, i, j, board, current_player):
    if i >= 0 and i < size: #check if the given i is within the board bounds
        if (j-1) >= 0: #check if its within the board bounds WEST
            if check_For_Freeing(size, (i), (j-1), board): #check for freed piece to the WEST of the captured NORTH/SOUTH piece
                board[i][j-1] = current_player #frees currentPlayers Alligatus
        if (j+1) < size: #check if its within the board bounds EAST
            if check_For_Freeing(size, (i), (j+1), board): #check for freed piece to the EAST of the captured NORTH/SOUTH piece
                board[i][j+1] = current_player #frees currentPlayers Alligatus

#check for freed pieces to the NORTH/SOUTH of the given piece
@jit(nopython=True)
def freed_Check_North_South_of_Piece(size, i, j, board, current_player):
    if j >= 0 and j < size: #check if the given i is within the board bounds
        if (i-1) >= 0: #check if its within the board bounds NORTH
            if check_For_Freeing(size, (i-1), (j), board): #check for freed piece to the NORTH of the captured WEST/EAST piece
                board[i-1][j] = current_player #frees currentPlayers Alligatus
        if (i+1) < size: #check if its within the board bounds SOUTH
            if check_For_Freeing(size, (i+1), (j), board): #check for freed piece to the SOUTH of the captured WEST/EAST piece
                board[i+1][j] = current_player #frees currentPlayers Alligatus

#check if piece on the given position has possibly been freed, returns true, if the piece has been freed, false if not (or there is no captured piece)
@jit(nopython=True)
def check_For_Freeing(size, i, j, board):
    if board[i][j] == 2 or board[i][j] == -2: #check if the given piece is captured
        enemy_value = int(board[i][j]*-0.5)
        if (j-1 >= 0 and j+1 < size and board[i][j-1] == enemy_value
                and board[i][j+1] == enemy_value): #check if WEST/EAST pieces does capture the given piece
            return False
        elif (i-1 >= 0 and i+1 < size and board[i-1][j] == enemy_value
                and board[i+1][j] == enemy_value): #check if NORTH/SOUTH pieces does capture the given piece
            return False
        else: #if there is not a capturing pair of enemy pieces, return true and free the captured piece
            return True
    return False

@jit(nopython=True)
def fast_utility(board, player):
    white_won = (board == -1).sum() < 2
    black_won = (board == 1).sum() < 2
    if player: # Player plays as white.
        if white_won:
            return 1
        elif black_won:
            return -1
    else: # Player plays as white.
        if black_won:
            return 1
        elif white_won:
            return -1
    return 0

class Latrunculi(Game):
    rand_seed_used = None
    action_type = "dual"

    def populate_board(self, seed):
        board = np.zeros((self.size, self.size), 'b')
        num_pieces = int((self.size * self.size) / 2)
        pieces = []
        if seed is not None:
            if seed != "random":
                self.rand_seed_used = seed
                np.random.seed(seed)
            # Generate random positions for pieces
            squares = np.arange(0, self.size * self.size)
            np.random.shuffle(squares)

            # Populate board with equal amount of white and black pieces
            for i in range(num_pieces):
                num = squares[i]
                Y = int(num / self.size)
                X = int(num % self.size)
                piece = 1 if i < num_pieces/2 else -1

                board[Y][X] = piece
                pieces.append((Y, X))
            pieces.sort()
        else:
            # Position pieces as a 'Chess formation'.
            board[:][0:2] = -1
            board[:][-2:] = 1
            pieces.extend([(0, x) for x in range(self.size)])
            pieces.extend([(1, x) for x in range(self.size)])
            pieces.extend([(self.size-2, x) for x in range(self.size)])
            pieces.extend([(self.size-1, x) for x in range(self.size)])

        self.init_state = State(board, True, pieces=pieces)

    def seed_used(self):
        super.__doc__
        return self.rand_seed_used

    def __init__(self, size, start_seed=None):
        self.init_state = None
        self.rand_seed_used = start_seed
        Game.__init__(self, size)
        self.num_actions = 80 # 4 (possible destinations for any piece) * 16 (board size) + 16 (remove enemy piece)

    def notify_observers(self, *args, **kwargs):
        for observer in self.__observers:
            observer.notify(self, *args, **kwargs)

    def start_state(self):
        super.__doc__
        if self.init_state is None:
            self.populate_board(self.rand_seed_used)
        return self.init_state

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        current_player = 0
        enemy_captured = 0
        if state.player:
            current_player = 1 #White
            enemy_captured = -2
        else:
            current_player = -1 #Black
            enemy_captured = 2
        actionsList = [] #we might have to add a pass option???

        for i, j in state.pieces:
            if state.board[i][j] == current_player:
                if i > 0:
                    actionsList.extend(check_North_Or_South_From_Player_Piece(self.size, i, j, -1, current_player, state.board)) #check for actions moving north
                if i+1 < self.size:
                    actionsList.extend(check_North_Or_South_From_Player_Piece(self.size, i, j, 1, current_player, state.board)) #check for actions moving south
                if j > 0:
                    actionsList.extend(check_West_Or_East_From_Player_Piece(self.size, i, j, -1, current_player, state.board)) #check for actions moving west
                if j+1 < self.size:
                    actionsList.extend(check_West_Or_East_From_Player_Piece(self.size, i, j, 1, current_player, state.board)) #check for actions moving east
            elif state.board[i][j] == enemy_captured: # if the current piece, is the opponents captured piece
                actionsList.append((i, j, i, j)) # action to remove an opponents captured piece

        if actionsList == []:
            actionsList.append(None)
        else:
            actionsList = [Action((x1, y1), (x2, y2)) for x1, y1, x2, y2 in actionsList]
        return actionsList

    def result(self, state, action):
        super.__doc__

        if action is None:
            return State(state.board, (not state.player), pieces=[p for p in state.pieces])
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
        new_state = State(newBoard, not state.player, [p for p in state.pieces])
        if state.board[source[0]][source[1]] == current_player: #if source is a piece owned by the current player
            if source[0] != dest[0] or source[1] != dest[1]: #check if source and dest are different
                i = dest[0]
                j = dest[1]
                newBoard[i][j] = current_player #moves piece to destination (dest)
                new_state.change_piece(source[0], source[1], i, j)
                newBoard[source[0]][source[1]] = 0 #removes piece from source
                workBoard = np.copy(newBoard) #workBoard is the one that is checked during the method

                #check if the move frees an opponents captured piece
                check_For_Freeing_Due_To_Move(self.size, source[0], source[1], newBoard, enemy_player)

                #check for suicide moves
                if (i-1) >= 0 and (i+1) < self.size: #check if possible suicide move is within board bounds NORTH/SOUTH
                    if workBoard[i-1][j] == enemy_player and workBoard[i+1][j] == enemy_player: #check for suicide move NORTH/SOUTH
                        #NORTH
                        if (i-2) >= 0: #check if suicide move capture, is within board bounds NORTH
                            if workBoard[i-2][j] == current_player: #check for suicide move capture NORTH
                                newBoard[i-1][j] = enemy_player*2 #captures the oppenents piece NORTH
                                freed_Check_West_East_of_Piece(self.size, (i-1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                        #SOUTH
                        if (i+2) < self.size: #check if suicide move capture, is within board bounds SOUTH
                            if workBoard[i+2][j] == current_player: #check for suicide move capture SOUTH
                                newBoard[i+1][j] = enemy_player*2 #captures the oppenents piece SOUTH
                                #check for freeing of another piece
                                freed_Check_West_East_of_Piece(self.size, (i+1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece

                if (j-1) >= 0 and (j+1) < self.size: #check if possible suicide move is within board bounds WEST/EAST
                    if workBoard[i][j-1] == enemy_player and workBoard[i][j+1] == enemy_player: #check for suicide move WEST/EAST
                        #WEST
                        if (j-2) >= 0: #check if suicide move capture, is within board bounds WEST
                            if workBoard[i][j-2] == current_player: #check for suicide move capture WEST
                                newBoard[i][j-1] = enemy_player*2 #captures the oppenents piece WEST
                                freed_Check_North_South_of_Piece(self.size, i, (j-1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                        #EAST
                        if (j+2) < self.size: #check if suicide move capture, is within board bounds EAST
                            if workBoard[i][j+2] == current_player: #check for suicide move capture EAST
                                newBoard[i][j+1] = enemy_player*2 #captures the oppenents piece EAST
                                freed_Check_North_South_of_Piece(self.size, i, (j+1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece

                #check for regular capture of enemies
                #NORTH
                if (i-2) >= 0: #check if possible regular capture is within board bounds NORTH
                    if workBoard[i-1][j] == enemy_player and workBoard[i-2][j] == current_player: #check for regular capture NORTH
                        newBoard[i-1][j] = enemy_player*2 #capture the opponents piece NORTH
                        freed_Check_West_East_of_Piece(self.size, (i-1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                #SOUTH
                if (i+2) < self.size: #check if possible regular capture is within board bounds SOUTH
                    if workBoard[i+1][j] == enemy_player and workBoard[i+2][j] == current_player: #check for regular capture SOUTH
                        newBoard[i+1][j] = enemy_player*2 #capture the opponents piece SOUTH
                        freed_Check_West_East_of_Piece(self.size, (i+1), j, newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                #WEST
                if (j-2) >= 0: #check if possible regular capture is within board bounds WEST
                    if workBoard[i][j-1] == enemy_player and workBoard[i][j-2] == current_player: #check for regular capture WEST
                        newBoard[i][j-1] = enemy_player*2 #capture the opponents piece WEST
                        freed_Check_North_South_of_Piece(self.size, i, (j-1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
                #EAST
                if (j+2) < self.size: #check if possible regular capture is within board bounds EAST
                    if workBoard[i][j+1] == enemy_player and workBoard[i][j+2] == current_player: #check for regular capture EAST
                        newBoard[i][j+1] = enemy_player*2 #capture the opponents piece EAST
                        freed_Check_North_South_of_Piece(self.size, i, (j+1), newBoard, current_player) #check for freeing of another piece, due to capture of enemy piece
            else:
                raise Exception("you attempted to move your piece, to the square where the piece started")
        elif state.board[source[0]][source[1]] == (enemy_player*2): #if source is an opponents captured piece
            if source[0] == dest[0] and source[1] == dest[1]: #if source and dest is equal, remove opponents captured piece
                newBoard[source[0]][source[1]] = 0 #removed captured piece
                new_state.change_piece(source[0], source[1], None, None)
            else:
                raise Exception("you have attempted to move an opponents captured piece...")
        else: #If none of the above, illegal move...
            raise Exception("you have attempted to move a piece that you do not own...")
        return new_state

    def terminal_test(self, state):
        super.__doc__
        return (state.board == 1).sum() < 2 or (state.board == -1).sum() < 2

    def utility(self, state, player):
        super.__doc__
        return fast_utility(state.board, player)

    def structure_data(self, state):
        super.__doc__

        pos_pieces = np.where(state.board == 1, state.board, np.zeros((self.size, self.size), dtype='b'))
        pos_captured = np.where(state.board == 2, state.board, np.zeros((self.size, self.size), dtype='b'))
        neg_pieces = -np.where(state.board == -1, state.board, np.zeros((self.size, self.size), dtype='b'))
        neg_captured = -np.where(state.board == -2, state.board, np.zeros((self.size, self.size), dtype='b'))

        # Structure data as a 4x4x4 stack.
        if state.player:
            return np.array([pos_pieces, pos_captured, neg_pieces, neg_captured])
        else:
            return np.array([neg_pieces, neg_captured, pos_pieces, pos_captured])

    def map_actions(self, actions, logits):
        """
        Map actions to neural network output policy logits. 
        Set all other logits to 0, since they represent illegal actions.
        """
        action_map = dict()
        move_logits = logits[0]
        remove_logits = logits[1]
        policy_sum = 0
        if actions[0] is None and len(actions) == 1:
            return action_map
        for action in actions:
            if action is None:
                continue
            y1, x1 = action.source
            y2, x2 = action.dest
            logit = 0
            if action.dest == action.source:
                # Action equals the removal of an enemy piece.
                logit = remove_logits[y1, x1]
            else:
                # Action equals a piece being moved.
                plane = move_logits[y1, x1]
                index = 0 if y1>y2 else 1
                if x1 != x2:
                    index = 2 if x1>x2 else 3

                logit = plane[index]
            action_map[action] = np.exp(logit)
            policy_sum += logit

        for action, policy in action_map.items():
            action_map[action] = policy/policy_sum if policy_sum else 0

        return action_map

    def map_visits(self, visits):
        """
        Map policy logits, for all states in the game, to
        board positions. This returns policies in the dimensions
        outputted by the neural network.
        """
        policy_moves = np.zeros((self.size, self.size, 4))
        policy_remove = np.zeros((self.size, self.size, 1))
        for a, p in visits.items():
            if a is None:
                continue
            y1, x1 = a.source
            y2, x2 = a.dest
            if a.dest == a.source:
                policy_remove[y1, x1] = p
            else:
                index = 0 if y1>y2 else 1
                if x1 != x2:
                    index = 2 if x1>x2 else 3

                policy_moves[y1, x1, index] = p
        return policy_moves, policy_remove
