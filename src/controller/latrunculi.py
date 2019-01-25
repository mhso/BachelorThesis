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
                            if board[i + direction][j + 2] == player: #check for possible suicide action to the west
                                actionsList.append(Action((i, j), (i+direction, j)))
                    else : #if there is no insta capture on this square, create action
                        actionsList.append(Action((i, j), (i+direction, j)))
                else :  #if there is no chance for insta capture, create action to empty square
                    actionsList.append(Action((i, j), (i+direction, j)))
            else : # if the north/south square contains a piece (either 1, 2, -1, -2), check for jumps
                for x in range((2*direction), (self.size*direction), (2*direction)):
                    if (i + x) >= 0 and (i + x) < self.size: #check that x squares north/south is within the bounds of the board
                        if board[i + (x + (-1*direction))][j] != 0: #check if there is a piece on the odd number square north/south... #this is a double check for the first jump, might want to optimize it...
                            if board[i + x][j] == 0: #checks for the even number square north/south being empty, if the square before was occupied
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
                for x in range((2*direction), (self.size*direction), (2*direction)):
                    if (j + x) >= 0 and (j + x) < self.size: #check that x squares WEST/EAST is within the bounds of the board
                        if board[i][j + (x + (-1*direction))] != 0: #check if there is a piece on the odd number square WEST/EAST... #this is a double check for the first jump, might want to optimize it...
                            if board[i][j + x] == 0: #checks for the even number square WEST/EAST being empty, if the square before was occupied
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
                #check for suicide moves
                if (i-1) >= 0 and (i+1) < self.size: #check if possible suicide move is within board bounds NORTH/SOUTH
                    if workBoard[i-1][j] == (currentPlayer*-1) and workBoard[i+1][j] == (currentPlayer*-1): #check for suicide move NORTH/SOUTH
                        if (i-2) >= 0: #check if suicide move capture, is within board bounds NORTH
                            if workBoard[i-2][j] == currentPlayer: #check for suicide move capture NORTH
                                newBoard[i-1][j] = (currentPlayer*-2) #captures the oppenents piece NORTH
                        if (i+2) < self.size: #check if suicide move capture, is within board bounds SOUTH
                            if workBoard[i+2][j] == currentPlayer: #check for suicide move capture SOUTH
                                newBoard[i+1][j] = (currentPlayer*-2) #captures the oppenents piece SOUTH
                if (j-1) >= 0 and (j+1) < self.size: #check if possible suicide move is within board bounds WEST/EAST
                    if workBoard[i][j-1] == (currentPlayer*-1) and workBoard[i][j+1] == (currentPlayer*-1): #check for suicide move WEST/EAST
                        if (j-2) >= 0: #check if suicide move capture, is within board bounds WEST
                            if workBoard[i][j-2] == currentPlayer: #check for suicide move capture WEST
                                newBoard[i][j-1] = (currentPlayer*-2) #captures the oppenents piece WEST
                        if (j+2) < self.size: #check if suicide move capture, is within board bounds EAST
                            if workBoard[i][j+2] == currentPlayer: #check for suicide move capture EAST
                                newBoard[i][j+1] = (currentPlayer*-2) #captures the oppenents piece EAST
                #check for regular capture of enemies
                if (i-2) >= 0: #check if possible regular capture is within board bounds NORTH
                    if workBoard[i-1][j] == (currentPlayer*-1) and workBoard[i-2][j] == currentPlayer: #check for regular capture NORTH
                        newBoard[i-1][j] = (currentPlayer*-2) #capture the opponents piece NORTH
                if (i+2) < self.size: #check if possible regular capture is within board bounds SOUTH
                    if workBoard[i+1][j] == (currentPlayer*-1) and workBoard[i+2][j] == currentPlayer: #check for regular capture SOUTH
                        newBoard[i+1][j] = (currentPlayer*-2) #capture the opponents piece SOUTH
                if (j-2) >= 0: #check if possible regular capture is within board bounds WEST
                    if workBoard[i][j-1] == (currentPlayer*-1) and workBoard[i][j-2] == currentPlayer: #check for regular capture WEST
                        newBoard[i][j-1] = (currentPlayer*-2) #capture the opponents piece WEST
                if (j+2) < self.size: #check if possible regular capture is within board bounds EAST
                    if workBoard[i][j+1] == (currentPlayer*-1) and workBoard[i][j+2] == currentPlayer: #check for regular capture EAST
                        newBoard[i][j+1] = (currentPlayer*-2) #capture the opponents piece EAST
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

    def terminal_test(self, state):
        super.__doc__
        return (state.board == 1).sum() == 1 or (state.board == -1).sum() == 1

    def utility(self, state, player):
        super.__doc__
        if player: # Player plays as white.
            return 0 if (state.board == 1).sum() == 1 else 1
        # Player plays as black.
        return 0 if (state.board == -1).sum() == 1 else 1
