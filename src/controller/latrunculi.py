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
                if state.board[i][j] == 1: #If the current piece on the board is owned by the current player 
                        actionsList.extend(self.checkNorthOrSouthFromPlayerPiece(i, j, -1, currentPlayer, state)) #check for actions moving north
                        actionsList.extend(self.checkNorthOrSouthFromPlayerPiece(i, j, 1, currentPlayer, state)) #check for actions moving south
                        actionsList.extend(self.checkWestOrEastFromPlayerPiece(i, j, -1, currentPlayer, state)) #check for actions moving west
                        actionsList.extend(self.checkWestOrEastFromPlayerPiece(i, j, -1, currentPlayer, state)) #check for actions moving east
                elif state.board[i][j] == (-2*currentPlayer): # if the current piece, is the opponents captured piece
                    actionsList.append(Action((i,j), (i,j))) # action to remove an opponents captured piece
        return actionsList

    # checks the squares north or south of a players piece, and acts accordingly
    def checkNorthOrSouthFromPlayerPiece(self, i, j, dir, player, state):
        actionsList = []
        if (i + dir) >= 0 and (i + dir) < self.size : # check for whether 1 square NORTH/SOUTH is within the board
            if state.board[i + dir][j] == 0: #check for NORTH/SOUTH square being empty
                if (j - 1) >= 0 and (j + 1) < self.size: #check for whether insta-capture is possible or if we are too close to edge of the board
                    if state.board[i + dir][j - 1] == (-1*player) and state.board[i + dir][j + 1] == (-1*player): #check for insta capture
                        if (j - 2) >= 0: #check whether there is room for possible suicide move to the west
                            if state.board[i + dir][j - 2] == player: #check for possible suicide action to the west
                                actionsList.append(Action((i,j), (i+dir,j)))
                        elif (j + 2) < self.size: #check whether there is room for possible suicide move to the east
                            if state.board[i + dir][j + 2] == player: #check for possible suicide action to the west
                                actionsList.append(Action((i,j), (i+dir,j)))
                    else : #if there is no insta capture on this square, create action
                        actionsList.append(Action((i,j), (i+dir,j)))
                else :  #if there is no chance for insta capture, create action to empty square
                    actionsList.append(Action((i,j), (i+dir,j)))
            else : # if the north/south square contains a piece (either 1, 2, -1, -2), check for jumps
                for x in range((2*dir), (self.size*dir), (2*dir)):
                    if (i + x) >= 0 and (i + x) < self.size: #check that x squares north/south is within the bounds of the board
                        if state.board[i + (x + (-1*dir))][j] != 0: #check if there is a piece on the odd number square north/south... #this is a double check for the first jump, might want to optimize it...
                            if state.board[i + x][j] == 0: #checks for the even number square north/south being empty, if the square before was occupied
                                actionsList.append(Action((i,j), (i+x,j))) #generate a jump action to the empty square
                            else:
                                break #jump chain is broken
                        else:
                            break #jump chain is broken
                    else:
                        break #break if outside of board bounds
        return actionsList

    # checks the squares west or east of a players piece, and acts accordingly
    def checkWestOrEastFromPlayerPiece(self, i, j, dir, player, state):
        actionsList = []
        if (j + dir) >= 0 and (j + dir) < self.size : # check for whether 1 square WEST/EAST is within the board
            if state.board[i][j + dir] == 0: #check for WEST/EAST square being empty
                if (i - 1) >= 0 and (i + 1) < self.size: #check for whether insta-capture is possible or if we are too close to edge of the board
                    if state.board[i - 1][j + dir] == (-1*player) and state.board[i + 1][j + dir] == (-1*player): #check for insta capture
                        if (i - 2) >= 0: #check whether there is room for possible suicide move to the north
                            if state.board[i - 2][j + dir] == player: #check for possible suicide action to the north
                                actionsList.append(Action((i,j), (i,j+dir)))
                        elif (i + 2) < self.size: #check whether there is room for possible suicide move to the south
                            if state.board[i + 2][j + dir] == player: #check for possible suicide action to the south
                                actionsList.append(Action((i,j), (i,j+dir)))
                    else : #if there is no insta capture on this square, create action
                        actionsList.append(Action((i,j), (i,j+dir)))
                else :  #if there is no chance for insta capture, create action to empty square
                    actionsList.append(Action((i,j), (i,j+dir)))
            else : # if the WEST/EAST square contains a piece (either 1, 2, -1, -2), check for jumps
                for x in range((2*dir), (self.size*dir), (2*dir)):
                    if (j + x) >= 0 and (j + x) < self.size: #check that x squares WEST/EAST is within the bounds of the board
                        if state.board[i][j + (x + (-1*dir))] != 0: #check if there is a piece on the odd number square WEST/EAST... #this is a double check for the first jump, might want to optimize it...
                            if state.board[i][j + x] == 0: #checks for the even number square WEST/EAST being empty, if the square before was occupied
                                actionsList.append(Action((i,j), (i,j+x))) #generate a jump action to the empty square
                            else:
                                break #jump chain is broken
                        else:
                            break #jump chain is broken
                    else:
                        break #break if outside of board bounds
        return actionsList

    def result(self, state, action):
        super.__doc__

    def terminal_test(self, state):
        super.__doc__
        return (state.board == 1).sum() == 1 or (state.board == -1).sum() == 1

    def utility(self, state, player):
        super.__doc__
        if player: # Player plays as white.
            return 0 if (state.board == 1).sum() == 1 else 1
        # Player plays as black.
        return 0 if (state.board == -1).sum() == 1 else 1
