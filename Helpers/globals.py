
from datetime import datetime
from models import Room

# key : websocket.id , value : Room object
rooms: dict[int,Room] = {}
# key : websocket.id , value : [ <room_id> , <player_name> ]
all_connections:dict[str,list[str,str]] = {}

# a list of all the games this server offers
AVAILABLE_GAMES = ["Tic Tac Toe","Connect 4"]