"""
---------------------------------------------------------------------
latrunculi: Subclass of game. Implements game methods for latrunculi.
---------------------------------------------------------------------
"""
import numpy as np
from controller.game import Game
from model.state import State, Action

class Latrunculi(Game):
    size = 8
    init_state = None

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

    def __init__(self, size, start_seed=None):
        Game.__init__(self)
        self.size = size
        self.populate_board(start_seed)

    def start_state(self):
        super.__doc__
        return self.init_state

    def player(self, state):
        super.__doc__
        return state.player

    def actions(self, state):
        super.__doc__
        currentPlayer = 0
        if state.player:
            currentPlayer = 1 #White
        else:
            currentPlayer = -1 #Black
        actionsList = [] #we might have to add a pass option???
        for i in range(self.size): #runs through the rows
            for j in range(self.size): #runs through the columns
                if state.board[i][j] == currentPlayer: #If the current piece on the board is owned by the current player 
                        actionsList.extend(self.checkNorthOrSouthFromPlayerPiece(i, j, -1, currentPlayer, state.board)) #check for actions moving north
                        actionsList.extend(self.checkNorthOrSouthFromPlayerPiece(i, j, 1, currentPlayer, state.board)) #check for actions moving south
                        actionsList.extend(self.checkWestOrEastFromPlayerPiece(i, j, -1, currentPlayer, state.board)) #check for actions moving west
                        actionsList.extend(self.checkWestOrEastFromPlayerPiece(i, j, 1, currentPlayer, state.board)) #check for actions moving east
                elif state.board[i][j] == (-2*currentPlayer): # if the current piece, is the opponents captured piece
                    actionsList.append(Action((i, j), (i, j))) # action to remove an opponents captured piece
        if actionsList == []:
            actionsList.append(None)
        return actionsList

    # checks the squares north or south of a players piece, and acts accordingly
    def checkNorthOrSouthFromPlayerPiece(self, i, j, direction, player, board): #perhaps just pass along the board????
        actionsList = []
        if (i + direction) >= 0 and (i + direction) < self.size: # check for whether 1 square NORTH/SOUTH is within the board
            if board[i + direction][j] == 0: #check for NORTH/SOUTH square being empty
                if (j - 1) >= 0 and (j + 1) < self.size: #check for whether insta-capture is possible or if we are too close to edge of the board
                    if board[i + direction][j - 1] == (-1*player) and board[i + direction][j + 1] == (-1*player): #check for insta capture
                        if (j - 2) >= 0: #check whether there is room for possible suicide move to the west
                            if board[i + direction][j - 2] == player: #check for possible suicide action to the west
                                actionsList.append(Action((i, j), (i+direction, j)))
                        elif (j + 2) < self.size: #check whether there is room for possible suicide move to the east
                            if board[i + direction][j + 2] == player: #check for possible suicide action to the east
                                actionsList.append(Action((i, j), (i+direction, j)))
                    else : #if there is no insta capture on this square, create action
                        actionsList.append(Action((i, j), (i+direction, j)))
                else :  #if there is no chance for insta capture, create action to empty square
                    actionsList.append(Action((i, j), (i+direction, j)))
            else : # if the north/south square contains a piece (either 1, 2, -1, -2), check for jumps
                for x in range((2*direction), (self.size*direction), (2*direction)): #Jump-loop
                    if (i + x) >= 0 and (i + x) < self.size: #check that x squares north/south is within the bounds of the board
                        if board[i + (x + (-1*direction))][j] != 0: #check if there is a piece on the odd number square north/south... #this is a double check for the first jump, might want to optimize it...
                            if board[i + x][j] == 0: #checks for the even number square north/south being empty, if the square before was occupied
                                if (j - 1) >= 0 and (j + 1) < self.size: #check if there is room for a possible insta-capture WEST/EAST
                                     if board[i + x][j - 1] == (-1*player) and board[i + x][j + 1] == (-1*player): #check for insta-capture west/east side
                                         break
                                         #i likely wont need the first check in the line below.... as that's checked further
                                elif (i + x - 1) >= 0 and (i + x + 1) < self.size: #check if there is room for a possible insta-capture NORTH/SOUTH
                                     if board[i + x - 1][j] == (-1*player) and board[i + x + 1][j] == (-1*player): #check for insta-capture west/east side
                                         break
                                actionsList.append(Action((i, j), (i+x, j))) #generate a jump action to the empty square
                            else:
                                break #jump chain is broken
                        else:
                            break #jump chain is broken
                    else:
                        break #break if outside of board bounds
        return actionsList

    # checks the squares west or east of a players piece, and acts accordingly
    def checkWestOrEastFromPlayerPiece(self, i, j, direction, player, board):
        actionsList = []
        if (j + direction) >= 0 and (j + direction) < self.size: # check for whether 1 square WEST/EAST is within the board
            if board[i][j + direction] == 0: #check for WEST/EAST square being empty
                if (i - 1) >= 0 and (i + 1) < self.size: #check for whether insta-capture is possible or if we are too close to edge of the board
                    if board[i - 1][j + direction] == (-1*player) and board[i + 1][j + direction] == (-1*player): #check for insta capture
                        if (i - 2) >= 0: #check whether there is room for possible suicide move to the north
                            if board[i - 2][j + direction] == player: #check for possible suicide action to the north
                                actionsList.append(Action((i, j), (i, j+direction)))
                        elif (i + 2) < self.size: #check whether there is room for possible suicide move to the south
                            if board[i + 2][j + direction] == player: #check for possible suicide action to the south
                                actionsList.append(Action((i, j), (i, j+direction)))
                    else: #if there is no insta capture on this square, create action
                        actionsList.append(Action((i, j), (i, j+direction)))
                else:  #if there is no chance for insta capture, create action to empty square
                    actionsList.append(Action((i, j), (i, j+direction)))
            else: # if the WEST/EAST square contains a piece (either 1, 2, -1, -2), check for jumps
                for x in range((2*direction), (self.size*direction), (2*direction)): #Jump-loop
                    if (j + x) >= 0 and (j + x) < self.size: #check that x squares WEST/EAST is within the bounds of the board
                        if board[i][j + (x + (-1*direction))] != 0: #check if there is a piece on the odd number square WEST/EAST... #this is a double check for the first jump, might want to optimize it...
                            if board[i][j + x] == 0: #checks for the even number square WEST/EAST being empty, if the square before was occupied
                                #i likely wont need the first check in the line below, as it is covered earlier
                                if (j + x - 1) >= 0 and (j + x + 1) < self.size: #check if there is room for a possible insta-capture WEST/EAST
                                     if board[i][j + x- 1] == (-1*player) and board[i][j + x + 1] == (-1*player): #check for insta-capture west/east side
                                         break
                                elif (i - 1) >= 0 and (i + 1) < self.size: #check if there is room for a possible insta-capture NORTH/SOUTH
                                     if board[i - 1][j + x] == (-1*player) and board[i + 1][j + x] == (-1*player): #check for insta-capture west/east side
                                         break
                                actionsList.append(Action((i, j), (i, j+x))) #generate a jump action to the empty square
                            else:
                                break #jump chain is broken
                        else:
                            break #jump chain is broken
                    else:
                        break #break if outside of board bounds
        return actionsList

    def result(self, state, action):
        super.__doc__
        if action is None:
            return State(state.board, (not state.player))
        source = action.source
        dest = action.dest
        currentPlayer = 0
        if state.player:
            currentPlayer = 1 #White
        else:
            currentPlayer = -1 #Black
        newBoard = np.copy(state.board) #newBoard is the one that will be returned
        if state.board[source[0]][source[1]] == currentPlayer: #if source is a piece owned by the current player
            if source[0] != dest[0] or source[1] != dest[1]: #check if source and dest are different
                i = dest[0]
                j = dest[1]
                newBoard[i][j] = currentPlayer #moves piece to destination (dest)
                newBoard[source[0]][source[1]] = 0 #removes piece from source
                workBoard = np.copy(newBoard) #workBoard is the one that is checked during the method

                #check if the move frees an opponents captured piece
                self.checkForFreeingDueToMove(source[0], source[1], newBoard, currentPlayer)

                #check for suicide moves
                if (i-1) >= 0 and (i+1) < self.size: #check if possible suicide move is within board bounds NORTH/SOUTH
                    if workBoard[i-1][j] == (currentPlayer*-1) and workBoard[i+1][j] == (currentPlayer*-1): #check for suicide move NORTH/SOUTH
                        #NORTH
                        if (i-2) >= 0: #check if suicide move capture, is within board bounds NORTH
                            if workBoard[i-2][j] == currentPlayer: #check for suicide move capture NORTH
                                newBoard[i-1][j] = (currentPlayer*-2) #captures the oppenents piece NORTH
                                self.freedCheckWestEastofPiece((i-1), j, newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece
                        #SOUTH
                        if (i+2) < self.size: #check if suicide move capture, is within board bounds SOUTH
                            if workBoard[i+2][j] == currentPlayer: #check for suicide move capture SOUTH
                                newBoard[i+1][j] = (currentPlayer*-2) #captures the oppenents piece SOUTH
                                #check for freeing of another piece
                                self.freedCheckWestEastofPiece((i+1), j, newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece

                if (j-1) >= 0 and (j+1) < self.size: #check if possible suicide move is within board bounds WEST/EAST
                    if workBoard[i][j-1] == (currentPlayer*-1) and workBoard[i][j+1] == (currentPlayer*-1): #check for suicide move WEST/EAST
                        #WEST
                        if (j-2) >= 0: #check if suicide move capture, is within board bounds WEST
                            if workBoard[i][j-2] == currentPlayer: #check for suicide move capture WEST
                                newBoard[i][j-1] = (currentPlayer*-2) #captures the oppenents piece WEST
                                self.freedCheckNorthSouthofPiece(i, (j-1), newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece
                        #EAST
                        if (j+2) < self.size: #check if suicide move capture, is within board bounds EAST
                            if workBoard[i][j+2] == currentPlayer: #check for suicide move capture EAST
                                newBoard[i][j+1] = (currentPlayer*-2) #captures the oppenents piece EAST
                                self.freedCheckNorthSouthofPiece(i, (j+1), newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece


                #check for regular capture of enemies
                #NORTH
                if (i-2) >= 0: #check if possible regular capture is within board bounds NORTH
                    if workBoard[i-1][j] == (currentPlayer*-1) and workBoard[i-2][j] == currentPlayer: #check for regular capture NORTH
                        newBoard[i-1][j] = (currentPlayer*-2) #capture the opponents piece NORTH
                        self.freedCheckWestEastofPiece((i-1), j, newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece
                #SOUTH
                if (i+2) < self.size: #check if possible regular capture is within board bounds SOUTH
                    if workBoard[i+1][j] == (currentPlayer*-1) and workBoard[i+2][j] == currentPlayer: #check for regular capture SOUTH
                        newBoard[i+1][j] = (currentPlayer*-2) #capture the opponents piece SOUTH
                        self.freedCheckWestEastofPiece((i+1), j, newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece
                #WEST
                if (j-2) >= 0: #check if possible regular capture is within board bounds WEST
                    if workBoard[i][j-1] == (currentPlayer*-1) and workBoard[i][j-2] == currentPlayer: #check for regular capture WEST
                        newBoard[i][j-1] = (currentPlayer*-2) #capture the opponents piece WEST
                        self.freedCheckNorthSouthofPiece(i, (j-1), newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece
                #EAST
                if (j+2) < self.size: #check if possible regular capture is within board bounds EAST
                    if workBoard[i][j+1] == (currentPlayer*-1) and workBoard[i][j+2] == currentPlayer: #check for regular capture EAST
                        newBoard[i][j+1] = (currentPlayer*-2) #capture the opponents piece EAST
                        self.freedCheckNorthSouthofPiece(i, (j+1), newBoard, currentPlayer) #check for freeing of another piece, due to capture of enemy piece
            else:
                raise Exception("you attempted to move your piece, to the square where the piece started")
        elif state.board[source[0]][source[1]] == (-2*currentPlayer): #if source is an opponents captured piece
            if source[0] == dest[0] and source[1] == dest[1]: #if source and dest is equal, remove opponents captured piece
                newBoard[source[0]][source[1]] = 0 #removed captured piece
            else:
                raise Exception("you have attempted to move an opponents captured piece...")
        else: #If none of the above, illegal move...
            raise Exception("you have attempted to move a piece that you do not own...")
        return State(newBoard, (not state.player))

    #checks whether moving a piece from its source, causes an enemys piece to be freed
    def checkForFreeingDueToMove(self, i, j, board, player):
        if (i-1) >= 0: #check that we are within board bounds
            if self.checkForFreeing((i-1), j, board): #checks piece NORTH of source
                board[i-1][j] = (player*-1) #frees piece
        if (i+1) < self.size: #check that we are within board bounds
            if self.checkForFreeing((i+1), j, board): #checks piece SOUTH of source
                board[i+1][j] = (player*-1) #frees piece
        if (j-1) >= 0: #check that we are within board bounds
            if self.checkForFreeing(i, (j-1), board): #checks piece WEST of source
                board[i][j-1] = (player*-1) #frees piece
        if (j+1) < self.size: #check that we are within board bounds
            if self.checkForFreeing(i, (j+1), board): #checks piece EAST of source
                board[i][j+1] = (player*-1) #frees piece

    #check for freed pieces to the WEST/EAST of the given piece
    def freedCheckWestEastofPiece(self, i, j, board, currentPlayer):
        if i >= 0 and i < self.size: #check if the given i is within the board bounds
            if (j-1) >= 0: #check if its within the board bounds WEST
                if self.checkForFreeing((i), (j-1), board): #check for freed piece to the WEST of the captured NORTH/SOUTH piece
                    board[i][j-1] = currentPlayer #frees currentPlayers Alligatus
            if (j+1) < self.size: #check if its within the board bounds EAST
                if self.checkForFreeing((i), (j+1), board): #check for freed piece to the EAST of the captured NORTH/SOUTH piece
                    board[i][j+1] = currentPlayer #frees currentPlayers Alligatus
    
    #check for freed pieces to the NORTH/SOUTH of the given piece
    def freedCheckNorthSouthofPiece(self, i, j, board, currentPlayer):
        if j >= 0 and j < self.size: #check if the given i is within the board bounds
            if (i-1) >= 0: #check if its within the board bounds NORTH
                if self.checkForFreeing((i-1), (j), board): #check for freed piece to the NORTH of the captured WEST/EAST piece
                    board[i-1][j] = currentPlayer #frees currentPlayers Alligatus
            if (i+1) < self.size: #check if its within the board bounds SOUTH
                if self.checkForFreeing((i+1), (j), board): #check for freed piece to the SOUTH of the captured WEST/EAST piece
                    board[i+1][j] = currentPlayer #frees currentPlayers Alligatus

    #check if piece on the given position has possibly been freed, returns true, if the piece has been freed, false if not (or there is no captured piece)
    def checkForFreeing(self, i, j, board):
        if board[i][j] == 2 or board[i][j] == -2: #check if the given piece is captured
            playerValue = (board[i][j]*0.5)
            if (j-1) >= 0 and (j+1) < self.size: #check for board bounds
                if board[i][j-1] == (playerValue*-1) and board[i][j+1] == (playerValue*-1): #check if WEST/EAST pieces does capture the given piece
                    return False
            elif (i-1) >= 0 and (i+1) < self.size: #check for board bounds
                if board[i-1][j] == (playerValue*-1) and board[i+1][j] == (playerValue*-1): #check if NORTH/SOUTH pieces does capture the given piece
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