# 3rd party libs
import numpy as np


class Connect4:
    '''
        player numbers -> [1,2]
        gameOver -> stores whether current game is over or not
        board -> the main board
        current_player 
    '''
    def __init__(self) -> None:
        self.players = [1,2]
        self.gameOver = False
        self.board = np.zeros([6,7]).astype(np.uint8)
        self.current_player = 0
    
    def prepareForNextGame(self):
        '''
            Prepare this object for the next game
        '''
        self.players = [1,2]
        self.gameOver = False
        self.board = np.zeros([6,7]).astype(np.uint8)
        self.current_player = self.current_player

    def play(self, move):
        '''
            Play the given move and return true is move was legal
        '''
        if  not isinstance(move,int):
            return False
        player_num = self.players[self.current_player]
        if 0 in self.board[:,move]:
            update_row = -1
            for row in range(1, self.board.shape[0]):
                update_row = -1
                if self.board[row, move] > 0 and self.board[row-1, move] == 0:
                    update_row = row-1
                elif row==self.board.shape[0]-1 and self.board[row, move] == 0:
                    update_row = row

                if update_row >= 0:
                    self.board[update_row, move] = player_num
                    self.current_player = (self.current_player + 1) % 2
                    break
            return True
        else:
            return False

    def game_drawn(self):
        '''
            Checks whether game is drawn or not
        '''
        return 0 not in self.board[0]

    def game_completed(self,player_ind):
        '''
            checks whther given player won or not
        '''
        player_num = self.players[player_ind] 
        player_win_str = '{0}{0}{0}{0}'.format(player_num)
        board = self.board
        to_str = lambda a: ''.join(a.astype(str))

        def check_horizontal(b):
            for row in b:
                if player_win_str in to_str(row):
                    return True
            return False

        def check_verticle(b):
            return check_horizontal(b.T)

        def check_diagonal(b):
            for op in [None, np.fliplr]:
                op_board = op(b) if op else b
                
                root_diag = np.diagonal(op_board, offset=0).astype(int)
                if player_win_str in to_str(root_diag):
                    return True

                for i in range(1, b.shape[1]-3):
                    for offset in [i, -i]:
                        diag = np.diagonal(op_board, offset=offset)
                        diag = to_str(diag.astype(int))
                        if player_win_str in diag:
                            return True

            return False

        return (check_horizontal(board) or
                check_verticle(board) or
                check_diagonal(board))