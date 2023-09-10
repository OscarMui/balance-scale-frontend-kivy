import asyncio
import aiohttp 
import websocket

from common.constants import SERVER_URL, WSS_URL, CLIENT_VERSION
from common.now import now
from common.sockets import sendMsg, recvMsgs, pingpong

class OnlineGame:
    # an event for receiving the success message after submitGuess
    guessSuccessEvent = asyncio.Event()

    # endTime and a lock for mutex
    # endTime = 0
    # startTime = 0
    # endTimeLock = asyncio.Lock()

    nickname = None
    gameInfo = None

    def __init__(self, qGame, qApp, nickname):
        self.qGame = qGame
        self.qApp = qApp
        self.nickname = nickname


    async def play(self):
        print("WS server:", WSS_URL)
        print("HTTP server:", SERVER_URL)
        print("Client version:", CLIENT_VERSION)

        try:

            TOKEN = await self.__obtainToken()

            print("finished obtainToken")

            # establish ws connection
            self.ws = websocket.create_connection(WSS_URL)

             # spawns off ping pong task
            self.pingPongTask = asyncio.create_task(pingpong(self.ws))

            # spawns off a task to put all msgs received in an event queue
            self.recvMsgsTask = asyncio.create_task(recvMsgs(self.ws, self.qGame))

            # consume the response of websocket connection feedback
            res = await self.qGame.get()
            if(res["result"]=="error"):
                print("result: error")
                self.qApp.put_nowait({
                    "event": "serverConnectionFailed",
                    "errorMsg": res["errorMsg"]
                })
                return
            assert(res["result"]=="success")
            pid = res["id"]

            print("Joined websocket")

            # send joinGame request
            sendMsg(self.ws,{
                "method": "joinGame",
                "nickname": self.nickname,
            })

            # wait for response
            res = await self.qGame.get()
            if(res["result"]=="error"):
                print("result: error")
                self.qApp.put_nowait({
                    "event": "serverConnectionFailed",
                    "errorMsg": res["errorMsg"]
                })
                return
            assert(res["result"]=="success")

            self.qApp.put_nowait({
                "event": "serverConnected",
                "participantsCount": res["participantsCount"],
                "participantsPerGame": res["participantsPerGame"],
            })

        except Exception as e:
            print("Exception",e)
            self.qApp.put_nowait({
                "event": "serverConnectionFailed",
                "errorMsg": str(e)
            })
            return

        # repeatedly get event from our own queue
        event = await self.qGame.get()

        while event["event"] != "gameStart":
            if(event["event"] == "quitGame"):
                return
            else:
                assert(event["event"] == "updateParticipantsCount")
                # forward this event to app
                self.qApp.put_nowait(event)
                event = await self.qGame.get()
        
        assert(event["event"]=="gameStart")

        # Find our own info
        ps = event["participants"]
        event["us"] = list(filter(lambda p: p["id"]==pid,ps))[0]

        gameInfo = event

        # forward gameStart event to app
        self.qApp.put_nowait(gameInfo)

        while not gameInfo["gameEnded"]:
            # acts as a middleman between the server and the UI
            event = await self.qGame.get() 
            while event["event"]!="gameInfo":
                if event["event"] == "submitGuess":
                    # this event is from the app, pass it on to the server
                    req = {
                        "method": "submitGuess",
                        "id": pid,
                        "guess": event["guess"],
                    }
                    sendMsg(self.ws,req)
                    res = await self.qGame.get()
                    while not "result" in res:
                        print(res)
                        # in case other events get in the way, enqueue the event again
                        self.qGame.put_nowait(res)
                        res = await self.qGame.get()
                    assert(res["result"]=="success")
                elif event["event"] == "participantDisconnectedMidgame":
                    # this event is from server, pass it on to app
                    self.qApp.put_nowait(event)
                else:
                    assert(event["event"] == "changeCountdown")
                    self.qApp.put_nowait(event)
                event = await self.qGame.get() 

            # Find our own info
            ps = event["participants"]
            event["us"] = list(filter(lambda p: p["id"]==id,ps))[0]

            gameInfo = event


    async def __obtainToken(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json"
            } 
            
            async with session.get(
                SERVER_URL + "/api/version"
            ) as resp:
                response = await resp.json()
                assert(response["result"]=="success")
                acceptedClientVersions = response["acceptedClientVersions"]
                if CLIENT_VERSION not in acceptedClientVersions:
                    raise Exception("VERSION ERROR: Incompatible version with server. Please obtain the latest code.")
                else:
                    print("Version compatible")
                networkDelay = now()-response["currentTime"]
                print("Network delay (ms): ",networkDelay)
                if networkDelay > response["allowedNetworkDelay"] or networkDelay < 0:
                    raise Exception(print("SYSTEM TIME ERROR: Your network connection is unstable, or your system time is wrong."))
                else:
                    print("Time in sync")

    def __del__(self):
        if hasattr(self,"pingPongTask"):
            self.pingPongTask.cancel()
        if hasattr(self,"recvMsgsTask"):
            self.recvMsgsTask.cancel()  
        if hasattr(self,"ws"):
            self.ws.close()
        print("onlineGame destructor finished")