from copy import copy
from datetime import datetime
from random import randint

from models import Player, Room
from .globals import rooms,all_connections,AVAILABLE_GAMES
from websockets import WebSocketCommonProtocol

MAX_PLAYERS = 6

def leaveRoom(websocket:WebSocketCommonProtocol):
    '''
        Removes this player from the room,
        If this player was last to leave, It deletes the room
        If this player was admin, then transfer the admin to some other student
    '''
    conIds = []
    to_delete = ""
    admin = ""
    web_id = websocket.id.__str__()
    # if web_id is in the connection
    if (all_connections.__contains__(web_id)):
        room_id,player_name = all_connections[web_id]
        if (rooms.__contains__(room_id)):
            room = rooms[room_id]
            
            to_delete = ""
            transferAdmin = False
            # checks if this player is present and is admin
            if room.players.__contains__(player_name):
                player = room.players[player_name]
                to_delete = player_name
                transferAdmin = player.isAdmin

            if to_delete != "":
                del room.players[to_delete]
            conIds = [p.connection for p in room.players.values()]
            if room.players.__len__() == 0:
                del rooms[room_id]
            elif transferAdmin:
                # transfer the admin 
                for key in room.players.keys():
                    first_key = key
                admin = first_key
                room.players[first_key].isAdmin = True # making any other player, the admin

        del all_connections[web_id]
    return conIds,to_delete,admin


def createRoom(request:dict[str,any], websocket:WebSocketCommonProtocol):
    '''
        Creates a room with the given object
    '''
    if not request.__contains__('room_id'):
        return {"type":"error","message":"room_id not provided"}
    if not request.__contains__('password'):
        return {"type":"error","message":"password not provided"}
    try:
        room_id = (int)(request['room_id'])
    except ValueError:
        room_id = randint(100000,999900)
    password = request['password']


    while (rooms.__contains__(room_id)):
        room_id = room_id + 1
    rooms[(room_id)] = Room(room_id, password)
    result,_ = addPlayer(request, websocket,True)
    if (result['type'] == "error"):
        return result

    res_room = rooms[room_id].json()
    res_room["device_player"] = result['data']['name']
    return {"type":"create_room","data":res_room}


def addPlayer(request:dict[str,str],websocket:WebSocketCommonProtocol,isAdmin = False):
    '''
        Add a player to the given room
    '''
    receipients = [websocket]
    if not request.__contains__('room_id'):
        return {"type":"error","message":"room_id not provided"},receipients
    if not request.__contains__('password'):
        return {"type":"error","message":"password not provided"},receipients
    if not request.__contains__('name'):
        return {"type":"error","message":"name not provided"},receipients
    room_id = request['room_id']
    password = request['password']
    name = request['name']


    if (not rooms.__contains__(room_id)):
        return {"type":"error","message":"room_id does not exists"},receipients
    room = rooms[room_id]
    if (room.password != password):
        return {"type":"error","message":"Wrong password"},receipients
    if (room.players.__len__() == MAX_PLAYERS):
        return {"type":"error","message":"Maximum players limit reached"},receipients
    c = 1
    while (room.players.__contains__(name)):
        name = name + str(c)
        c +=1
    
    player = Player(name,websocket,isAdmin)

    receipients = [p.connection for p in room.players.values()]
    room.players[name] = player
    all_connections[websocket.id.__str__()] = [room_id, name]
    
    res_room = room.json()
    res_room["device_player"] = player.json()['name']
    return {
        "type":"add_player",
        "data":player.json(),
        "room":res_room
    },receipients


def initialize(request:dict[str,str], websocket:WebSocketCommonProtocol):
    '''
        A request to initialize the board
        This requires player to be admin
    '''
    recepient = [websocket]
    if not request.__contains__('players'):
        return [{"type":"error","message":"players not provided"}],[recepient]
    if not request.__contains__('gameName'):
        return [{"type":"error","message":"gameName not provided"}],[recepient]
    players:list[str] = request['players']
    gameName = request['gameName']

    if len(players) != 2:
        return [{"type":"error","message":"There must be exactly 2 players"}],[recepient]
    if players[0] == players[1]:
        return [{"type":"error","message":"Both players cannot be same."}],[recepient]
    if gameName not in AVAILABLE_GAMES:
        return [{"type":"error","message":f"This game is not available. Avalable games are: [{AVAILABLE_GAMES}"}],[recepient]


    web_id = websocket.id.__str__()
    if (not all_connections.__contains__(web_id)):
        return [{"type":"error","message":"This connection isn't associated with any room"}],[recepient]
    room_id,player_name = all_connections[web_id]

    if (not rooms.__contains__(room_id)):
        del all_connections[web_id]
        return [{"type":"error","message":"This connection isn't associated with any room"}],[recepient]
    room = rooms[room_id]

    if (not room.players.__contains__(player_name)):
        del all_connections[web_id]
        return [{"type":"error","message":"This Player is not present in its associated room."}],[recepient]



    selected_players:list[str] = []
    watchers:list[str] = []
    selected_players_sockets = []
    if not room.players[player_name].isAdmin:
        return [{"type":"error","message":"Can't process this request. Please ask admin to start the game."}],[recepient]
    
    players_update:dict[str,str] = {}
    
    for p in room.players.values():
        if p.name in players:
            p.role = f"player{players.index(p.name)}"
            selected_players.append(p.name)
            selected_players_sockets.append(p.connection)
        else:
            p.role = "watcher"
            watchers.append(p.name)
        players_update[p.name] = p.role

    
    if len(players) != 2:
        return [{"type":"error","message":"Can't find the mentioned players."}],[recepient]
    
    room.currGame.players = []
    room.currGame.watchers = watchers
    room.currGame.waiting = selected_players
    room.currGame.gameObjtoNone()
    room.currGame.gameName = gameName

    if player_name in selected_players:
        selected_players.remove(player_name)
        room.currGame.players.append(player_name)
        selected_players_sockets.remove(room.players[player_name].connection)
    
    connectedIds = [p.connection for p in room.players.values()]

    return [{"type":"ready","data":gameName},{"type":"role_update","roles":players_update}],[list(selected_players_sockets), connectedIds]

def player_ready(request:dict[str,str], websocket:WebSocketCommonProtocol):
    '''
        Player declares "am ready".
        returns either of two message, either to create and start a new room or 
        wait for other players
    '''
    recepient = [websocket]
    web_id = websocket.id.__str__()
    if (not all_connections.__contains__(web_id)):
        return {"type":"error","message":"This connection isn't associated with any room"},recepient
    room_id, player_name = all_connections[web_id]

    if (not rooms.__contains__(room_id)):
        del all_connections[web_id]
        return {"type":"error","message":"This connection isn't associated with any room"},recepient
    room = rooms[room_id]


    if (not room.players.__contains__(player_name)):
        del all_connections[web_id]
        return {"type":"error","message":"This Player is not present in its associated room."},recepient

    game = room.currGame
    if (player_name in game.waiting):
        game.waiting.remove(player_name)

    game.players.append(player_name)
    connectedIds = [room.players[p].connection for p in (list(game.players) + list(game.watchers))] # all except those who are in waiting

    if (len(game.waiting) != 0):
        return {"type":"loading","message":f"Waiting for players to get ready: {len(game.waiting)} remaining."},connectedIds
    
    # start the game

    game.intializeGame()    
    if not game.gameObjIsNone():
        return {"type":"create_board","data":{"game":game.gameName,"current_player":game.currentPlayer()}},connectedIds
    else:
        return {"type":"error","message":"This Player is not present in its associated room."},recepient
    
def play(request:dict[str,str], websocket:WebSocketCommonProtocol):
    '''
        Plays a move. This can only be used by a "player",admin also cannot
        use this, if he is not a player for the currentGame
    '''
    recepient = [websocket]
    if not request.__contains__('move'):
        return [{"type":"error","message":"move not provided"}],recepient
    
    move = request['move']

    web_id = websocket.id.__str__()
    if (not all_connections.__contains__(web_id)):
        return [{"type":"error","message":"This connection isn't associated with any room"}],recepient
    room_id,player_name = all_connections[web_id]
    

    if (not rooms.__contains__(room_id)):
        del all_connections[web_id]
        return [{"type":"error","message":"This connection isn't associated with any room"}],recepient
    room = rooms[room_id]

    if (not room.players.__contains__(player_name)):
        del all_connections[web_id]
        return [{"type":"error","message":"This Player is not present in its associated room."}],recepient


    game = room.currGame
    if not game.isPlayer(player_name):
        return [{"type":"error","message":"You are an audience for this game."}],recepient
    
    # print(room.players[player_name].role,f"player{game.currentPlayer()}")
    if room.players[player_name].role != f"player{game.currentPlayer()}":
        return [{"type":"error","message":"This is not your turn"}],recepient
    

    currPlayer = game.currentPlayer()
    result = game.playGame(move)
    if (result):
        to_send = [{"type":"play","data":{"move":move,"current_player":currPlayer}}]
        player_won = game.won(currPlayer)
        if player_won:
            # sends a won request and then a request to re create the board
            updatePlayers(player_name,copy(game.players),room.players)
            all_players = room.json()['players']
            to_send.append({"type":'won',"data": {"won":player_name,"currPlayer":currPlayer,"all_players":all_players}})
            to_send.append({"type":"create_board","data":{"game":game.gameName,"current_player":game.currentPlayer()}})

        elif game.gameDrawn():
            # draw request and then re create the board
            to_send.append({"type":"draw"})
            to_send.append({"type":"create_board","data":{"game":game.gameName,"current_player":game.currentPlayer()}})

        
        connectedIds = [p.connection for p in room.players.values()]
        return to_send,connectedIds
    else:
        return [{"type":"error","message":"Invalid move"}],recepient
    
def updatePlayers(player_won:str,playing:list[str],all_players:dict[str,Player]):
    '''
        Helper function to update the players with won and lost
    '''
    playing.remove(player_won)
    lost_players = playing
    for ply in lost_players:
        if not all_players.__contains__(ply):
            continue
        player = all_players[ply]
        player.lost +=1

    all_players[player_won].won +=1

        

def cancelGame(request:dict[str,str], websocket:WebSocketCommonProtocol):
    '''
        Cancels the game and send a request to all the players 
        in the room to cancel the game.
    '''
    recepient = [websocket]
    web_id = websocket.id.__str__()
    if (not all_connections.__contains__(web_id)):
        return {"type":"error","message":"This connection isn't associated with any room"},recepient
    room_id, player_name = all_connections[web_id]

    if (not rooms.__contains__(room_id)):
        del all_connections[web_id]
        return {"type":"error","message":"This connection isn't associated with any room"},recepient
    room = rooms[room_id]

    if (not room.players.__contains__(player_name)):
        del all_connections[web_id]
        return {"type":"error","message":"This Player is not present in its associated room."},recepient

    cancel = False
    name = ""
    if room.currGame.isPlayer(player_name):
        cancel = True
        name = "a player"
    elif player_name in room.currGame.waiting:
        cancel = True
        name = ": A player(refused to join)"
    elif room.players[player_name].isAdmin:
        cancel = True
        name = "Admin"

    if cancel:
        connectedIds = [p.connection for p in room.players.values()]
        return {"type":"cancel","message":f"Game cancelled by {name}"},connectedIds
    else:
        return {"type":"error","message":"You are neither player nor admin"},recepient


def allConnected():
    '''
        return list of all the websockets connected to this server
    '''
    connectedIds = []
    for _,info in all_connections.items(): 
        room_id,player_name = info
        if (rooms.__contains__(room_id)):
            room = rooms[room_id]
            if room.players.__contains__(player_name):
                connectedIds.append(room.players[player_name].connection)

    return connectedIds

            



@DeprecationWarning
def assignWatcher(request:dict[str,str],websocket:WebSocketCommonProtocol) -> tuple[dict,list[WebSocketCommonProtocol]]:
    receipients = [websocket]
    if not request.__contains__('name'):
        return {"type":"error","message":"name not provided"},receipients
    web_id = websocket.id.__str__()
    if (not all_connections.__contains__(web_id)):
        return {"type":"error","message":"this connection is not registered on our servers"},receipients
    
    room_id, player_name = all_connections[web_id]
    room = rooms[room_id]
    name = request['name']

    if not room.players.__contains__(name):
        return {"type":"error","message":f'Given name ${name} does not belong to this room.'},receipients

    for _,p in room.players.items():
        if (p.connection == websocket):
            if p.isAdmin:
                player = room.players[name]
                player_con = player.connection
                game = room.currGame
                game.watchers.append(player_con)
                player.role = "Watcher"

                if (player_con in game.players):
                    game.players.remove(player_con)
                receipients = [p.connection for p in room.players.values()]
                return {"type":"make_watcher","data":name},receipients
            
            else:
                return {"type":"error","message":"Only admins can change the roles"},receipients
            
    del all_connections[web_id]
    return {"type":'error',"message":"This connection is not registered to given room_id"},receipients

@DeprecationWarning
def assignPlayer(request:dict[str,str],websocket:WebSocketCommonProtocol):
    recepients = [websocket]
    if not request.__contains__('name'):
        return {"type":"error","message":"name not provided"},recepients
    
    web_id = websocket.id.__str__()
    if (not all_connections.__contains__(web_id)):
        return {"type":"error","message":"this connection is not registered on our servers"},recepients
    
    room_id,_ = all_connections[web_id]
    room = rooms[room_id]
    name = request['name']
    
    if not room.players.__contains__(name):
        return {"type":"error","message":f'Given name ${name} does not belong to this room.'},recepients

    for _,p in room.players.items():
        if (p.connection == websocket):
            if p.isAdmin:
                player = room.players[name]
                player_con = player.connection
                game = room.currGame
                if (game.players.__len__() >= 2):
                    return {"type":"error","message":"There are already 2 players.Consider assigning some/any player, a watcher role."},recepients
                game.players.append(player_con)
                player.role = "Player"

                if (player_con in game.watchers):
                    game.watchers.remove(player_con)
                recepients = [p.connection for p in room.players.values()]
                return {"type":"make_player","data":name},recepients
            
            else:
                return {"type":"error","message":"Only admin can change the roles"},recepients
            
    del all_connections[web_id]
    return {"type":'error',"message":"This connection is not registered to given room_id"},recepients

