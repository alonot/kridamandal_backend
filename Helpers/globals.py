
from datetime import datetime
from models import Room
rooms: dict[int,Room] = {}
all_connections:dict[str,list[str,str]] = {}
prevDelete = datetime.now()

AVAILABLE_GAMES = ["Tic Tac Toe","Connect 4"]