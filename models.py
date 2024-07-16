'''
    Dummy class depicting a player
'''
from datetime import datetime

from websockets import WebSocketCommonProtocol
from Helpers.Connect4 import Connect4
from Helpers.TicTacToe import TicTacToe

class Player:
    name:str
    joined_at:str
    isAdmin:bool
    connection:WebSocketCommonProtocol
    won:int
    lost:int
    role: str

    def __init__(self, name:str, websocket: WebSocketCommonProtocol,isAdmin:bool) -> None:
        self.name =  name
        self.isAdmin = isAdmin
        self.joined_at =  (datetime.now().replace(microsecond=0).__str__())
        self.won = 0
        self.lost = 0
        self.role = "Watcher"
        self.connection = websocket

    def json(self) -> dict:
        return{
            "name":self.name,
            "joined_at":self.joined_at,
            "won":self.won,
            "lost":self.lost,
            "admin":self.isAdmin,
            "role":self.role
        }

class Game:
    players:list[str]
    watchers: list[str]
    waiting:list[str]
    gameName: str
    __gameObj: Connect4 | TicTacToe | None

    def __init__(self) -> None:
        self.players = []
        self.watchers = []
        self.waiting = []
        self.gameName = ""
        self.__gameObj= None

    def gameObjIsNone(self):
        return self.__gameObj is None
    
    def gameObjtoNone(self):
        self.__gameObj = None

    def isPlayer(self,player_name:str):
        return player_name in self.players

    def intializeGame(self):
        match(self.gameName):
            case "Tic Tac Toe":
                self.__gameObj = TicTacToe()
                pass
            case "Connect 4":
                self.__gameObj = Connect4()
                pass
            case _:
                self.board = None
                return None
        
    def currentPlayer(self):
        return self.__gameObj.current_player
    
    def playGame(self,move:any):

        match(self.gameName):
            case "Tic Tac Toe":
                return self.__gameObj.play(move)
            
            case "Connect 4":
                return self.__gameObj.play(move)
                
            case _:
                self.board = None
                return None

    def won(self,player_ind):
        res = self.__gameObj.game_completed(player_ind)
        if res:
            self.__gameObj.prepareForNextGame()
        return res
    
    def gameDrawn(self):
        return self.__gameObj.game_drawn()

'''
    class depicting single object in the 'room' map.
'''
class Room:
    room_id:int
    password:str
    players:dict[str,Player]
    currGame: Game
    board:any
    lastSeen: datetime

    def __init__(self,room_id,password) -> None:
        self.room_id = (room_id)
        self.password = password
        self.currGame = Game()
        self.players = {}
        self.lastSeen = datetime.now()    

    def json(self) -> dict:
        return {
            "room_id": self.room_id,
            "players": [p.json() for p in self.players.values()],
        }
    
