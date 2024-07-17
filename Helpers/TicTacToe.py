# 3rd party libs
import numpy as np

#https://stackoverflow.com/a/37737985
# def turn_worker(board, send_end, p_func):
#     send_end.send(p_func(board))


class TicTacToe:
    '''
        player numbers -> [1,2]
        filled_blocks -> Helps in determining if game is drawn or not
        board -> the main board
        current_player 
    '''
    def __init__(self) -> None:
        self.players = [1,2]
        self.filled_blocks = 0
        self.board = np.zeros([3,3]).astype(np.uint8)
        self.current_player = 0
    
    def prepareForNextGame(self):
        '''
            Prepare this object for the next game
        '''
        self.players = [1,2]
        self.filled_blocks = 0
        self.board = np.zeros([3,3]).astype(np.uint8)
        self.current_player = self.current_player

    def play(self, move):
        '''
            Play the given move and return true is move was legal
        '''
        if  not isinstance(move,list):
            return False
        player_num = self.players[self.current_player]
        if self.board[move[0],move[1]] == 0:
            self.board[move[0],move[1]] = player_num
            self.filled_blocks +=1
            self.current_player = (self.current_player + 1) % 2
            return True
        else:
            return False

    def game_drawn(self):
        '''
            Checks whether game is drawn or not
        '''
        return self.filled_blocks == 9

    def game_completed(self,player_ind):
        '''
            checks whther given player won or not
        '''
        player_num = self.players[player_ind] 
        player_win_str = '{0}{0}{0}'.format(player_num)
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

            return False

        return (check_horizontal(board) or
                check_verticle(board) or
                check_diagonal(board))