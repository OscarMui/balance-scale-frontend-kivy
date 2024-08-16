import asyncio
import httpx

from common.constants import SERVER_URL, WSS_URL, CLIENT_VERSION
from common.now import now
from common.socket import Socket

class OnlineGame:
    # an event for receiving the success message after submitGuess
    # guessSuccessEvent = asyncio.Event()

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
            if(res["result"]=="appError"):
                print("result: appError")
                self.qApp.put_nowait({
                    "event": "serverConnectionFailed",
                    "errorMsg": res["errorMsg"]
                })
                return
            assert(res["result"]=="success")

            print("Joined websocket")

            # send joinGame request
            self.socket.sendMsg({
                "method": "joinGame",
                "nickname": self.nickname,
            })

            # wait for response
            res = await self.qGame.get()
            print("onlineGame response",res)
            if(res["result"]=="appError"):
                print("result: appError")
                self.qApp.put_nowait({
                    "event": "serverConnectionFailed",
                    "errorMsg": res["errorMsg"]
                })
                return
            assert(res["result"]=="success")
            pid = res["id"]

            msg = {
                "event": "serverConnected",
                "participantsCount": res["participantsCount"],
                "participantsPerGame": res["participantsPerGame"],
            }

            self.qApp.put_nowait(msg)

            print("finished sending serverConnected event",msg)

        except Exception as e:
            print("Exception in onlineGame (before serverConnected)",repr(e))
            self.qApp.put_nowait({
                "event": "serverConnectionFailed",
                "errorMsg": repr(e)
            })
            return

        try:
            # repeatedly get event from our own queue
            event = await self.qGame.get()

            while event["event"] != "gameStart":
                if(event["event"] == "quitGame" or event["event"] == "appError"):
                    return
                elif(event["event"] == "gameError"):
                    # forward this event to app
                    print("forwarded to qApp")
                    self.qApp.put_nowait(event)
                    # then stop
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
            event["mode"] = "online"

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
                    elif(event["event"] == "gameError"):
                        # forward this event to app
                        self.qApp.put_nowait(event)
                        # then stop
                        return
                    elif(event["event"] == "appError"):
                        return
                    else:
                        assert(event["event"] == "participantDisconnectedMidgame" or 
                               event["event"] == "changeCountdown")
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
                event["mode"] = "online"

                gameInfo = event
                # inform the UI
                self.qApp.put_nowait(gameInfo)
        except Exception as e:
            print("Exception in onlineGame (after serverConnected)",repr(e))
            self.qApp.put_nowait({
                "event": "gameError",
                "errorMsg": repr(e)
            })
            return

    async def __obtainToken(self):
        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(5.0, read=15.0)
            resp = await client.get(SERVER_URL + "/api/version", timeout=timeout)
            response = resp.json()
            assert(response["result"]=="success")
            acceptedClientVersions = response["acceptedClientVersions"]
            if CLIENT_VERSION not in acceptedClientVersions:
                raise Exception("VERSION ERROR: Incompatible version with server. You need to update the app in order to play online.")
            else:
                print("Version compatible")
            return None

    def __del__(self):
        if(hasattr(self,"socket")):
            # call destructor of the socket
            self.socket.stop()
        print("onlineGame destructor finished")