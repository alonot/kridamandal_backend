import asyncio
import inspect
import json
import os
import signal
import websockets
from websockets import WebSocketCommonProtocol
from Helpers.RoomFunction import createRoom,addPlayer,leaveRoom,assignPlayer,assignWatcher,\
play,initialize,player_ready,cancelGame,allConnected


async def handler(websocket:WebSocketCommonProtocol):
    try:
        async for message in websocket: # this is a blocking call, for loop waits here asynchronously for next messages

            msg:dict = json.loads(message)
            result = []
            broadcast = False
            connecteds = [websocket]
            sleep = False
            # print(msg)
            match(msg["type"]):
                case "create":
                    result = [(createRoom(msg,websocket))]
                    broadcast = False

                case "add_player":
                    res,connecteds = addPlayer(msg,websocket)
                    if res['type'] != 'error':
                        # create room request to this player and then 
                        # pass the result to broadcast other players that new player
                        # joined
                        await websocket.send(json.dumps({
                            "type":"create_room",
                            "data":res['room']
                        }))
                        del res['room']
                        result = [res]
                        broadcast = True
                    else:
                        result = [res]
                        broadcast = False


                case "make_watcher":
                    res,connecteds = assignWatcher(msg,websocket)
                    result = [res]
                    broadcast = True

                case "make_player":
                    res,connecteds = assignPlayer(msg,websocket)
                    result = [res]
                    broadcast = True

                case "initialize":
                    res, connecteds = initialize(msg,websocket)
                    if len(res) == 2:
                        # broadcast this message,
                        # role update, message to all the connectedIds
                        res_broad = res[1]
                        ids = connecteds[1]
                        websockets.broadcast(ids,json.dumps(res_broad))
                    # then broadcast a request to ask for ready only to the players
                    connecteds = connecteds[0]
                    result = [res[0]]
                    broadcast = True
                    

                case "player_ready":
                    res, connecteds = player_ready(msg,websocket)
                    result = [res]
                    broadcast = True

                case "play":
                    res, connecteds = play(msg,websocket)
                    result = res
                    broadcast = True
                    if (res[0]['type'] != "error"):
                        # sleep of 3s so that won message is displayed properly
                        sleep = True

                case "cancel":
                    res, connecteds = cancelGame(msg,websocket)
                    result = [res]
                    broadcast = True
                case _:
                    pass

            # print("result",result,broadcast)
            for r in result:
                try:
                    if (broadcast):
                        websockets.broadcast(connecteds,json.dumps(r))
                    else:
                        await websocket.send(json.dumps(r))  
                    if sleep:
                        await asyncio.sleep(3)
                except TypeError:
                    pass
                

    except websockets.ConnectionClosedOK:
        conIds,name,admin = leaveRoom(websocket)
        if name != "":
            if (websocket in conIds):
                conIds.remove(websocket)
            websockets.broadcast(conIds,json.dumps({"type":"remove_player","data":{"name":name,"admin":admin}}))
        # print("LEAVEING")

    except websockets.ConnectionClosedError as e:
        conIds,name,admin = leaveRoom(websocket)
        if name != "":
            if (websocket in conIds):
                conIds.remove(websocket)
            websockets.broadcast(conIds,json.dumps({"type":"remove_player","data":{"name":name,"admin":admin}}))
        # print("LEAVEING with error:",e)

    except Exception as e:
        print(e)
        await websocket.send(json.dumps({"type":"error","message":"Internal server error"}))

    finally:
        conIds,name,admin = leaveRoom(websocket)
        if name != "":
            if (websocket in conIds):
                conIds.remove(websocket)
            websockets.broadcast(conIds,json.dumps({"type":"remove_player","data":{"name":name,"admin":admin}}))
        # print("Finally")

async def broadcastShutdown(stop):
    try:
        ids = allConnected()
        message = json.dumps({"type":"disconnected"})
        await websockets.broadcast(ids,message)
    except Exception as e:
        pass
    finally:
        stop.set_result()

def handleSigTerm(stop):
    asyncio.create_task(broadcastShutdown(stop))

async def main():
    DEBUG = False
    if DEBUG:
        async with websockets.serve(handler, "", 8001):
            await asyncio.Future()  # this will run forever
    else:
        # Set the stop condition when receiving SIGTERM.
        loop = asyncio.get_running_loop()
        stop = loop.create_future()
        loop.add_signal_handler(signal.SIGTERM, handleSigTerm, stop) # not for windows

        port = int(os.environ.get("PORT", "8001"))
        async with websockets.serve(handler, "", port):
            await stop # this will run forever
    




if __name__ == "__main__":
    

    
    print("establishing")
    asyncio.run(main())   # It creates an asyncio event loop, 
    # runs the main() coroutine, and shuts down the loop.