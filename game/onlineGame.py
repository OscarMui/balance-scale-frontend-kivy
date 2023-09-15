import asyncio
import httpx

from common.constants import SERVER_URL, WSS_URL, CLIENT_VERSION
from common.now import now
from common.socket import Socket

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
            self.socket = Socket(WSS_URL,self.qGame)

            # consume the response of websocket connection feedback
            res = await self.qGame.get()
            print("onlineGame response",res)
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
            self.socket.sendMsg({
                "method": "joinGame",
                "nickname": self.nickname,
            })

            # wait for response
            res = await self.qGame.get()
            print("onlineGame response",res)
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

            print("finished sending serverConnected event")

        except Exception as e:
            print("Exception in onlineGame",e)
            self.qApp.put_nowait({
                "event": "serverConnectionFailed",
                "errorMsg": repr(e)
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
        p = list(filter(lambda p: p["id"]==pid,ps))[0]
        p["nickname"] = p["nickname"] + " (YOU)"
        event["us"] = p
        event["roundStartTime"] += now()
        event["roundEndTime"] += now()

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
                    self.socket.sendMsg(req)
                    res = await self.qGame.get()
                    while not "result" in res:
                        # print(res)
                        # in case other events get in the way, enqueue the event again
                        self.qGame.put_nowait(res)
                        res = await self.qGame.get()
                        await asyncio.sleep(0.1) # necessary or else it will enter an infinite loop when waiting for the response, so the response cannot get through
                    assert(res["result"]=="success")
                elif event["event"] == "participantDisconnectedMidgame":
                    # this event is from server, pass it on to app
                    self.qApp.put_nowait(event)
                else:
                    assert(event["event"] == "changeCountdown")
                    # this event is from server, pass it on to app
                    self.qApp.put_nowait(event)

                event = await self.qGame.get() 

            # Find our own info
            ps = event["participants"]
            p = list(filter(lambda p: p["id"]==pid,ps))[0]
            p["nickname"] = p["nickname"] + " (YOU)"
            event["us"] = p
            event["roundStartTime"] += now()
            event["roundEndTime"] += now()

            gameInfo = event
            # inform the UI
            self.qApp.put_nowait(gameInfo)


    async def __obtainToken(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(SERVER_URL + "/api/version", timeout=10.0)
            response = resp.json()
            assert(response["result"]=="success")
            acceptedClientVersions = response["acceptedClientVersions"]
            if CLIENT_VERSION not in acceptedClientVersions:
                raise Exception("VERSION ERROR: Incompatible version with server. Please obtain the latest code.")
            else:
                print("Version compatible")
            networkDelay = now()-response["currentTime"]
            print("Network delay (ms): ",networkDelay)
            if networkDelay > response["allowedNetworkDelay"] or networkDelay < 0:
                # raise Exception("SYSTEM TIME ERROR: Your network connection is unstable, or your system time is wrong.")
                # Disable clock check for now, probably has to figure out another method
                print("SYSTEM TIME ERROR: Your network connection is unstable, or your system time is wrong.")
            else:
                print("Time in sync")

    def __del__(self):
        if(hasattr(self,"socket")):
            # call destructor of the socket
            self.socket.stop()
        print("onlineGame destructor finished")