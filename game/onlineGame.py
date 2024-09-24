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

    def __init__(self, qGame, qApp, store, nickname=None, pid=None):
        assert(not (nickname==None and pid == None))
        self.qGame = qGame
        self.qApp = qApp
        self.nickname = nickname
        self.store = store
        self.pid = pid
        self.isReconnect = self.nickname == None


    async def play(self):
        print("WS server:", WSS_URL)
        print("HTTP server:", SERVER_URL)
        print("Client version:", CLIENT_VERSION)

        try:

            TOKEN = await self.__getToken()

            print("finished __getToken")

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

            print("Joined websocket")

        except Exception as e:
            print("Exception in onlineGame (getToken and initial connection)",repr(e))
            self.qApp.put_nowait({
                "event": "serverConnectionFailed",
                "errorMsg": repr(e)
            })
            return
        


        if not self.isReconnect:
            try:
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
                self.pid = res["id"]

                self.store.put('pidV1', value=self.pid)

                msg = {
                    "event": "serverConnected",
                    "participantsCount": res["participantsCount"],
                    "participantsPerGame": res["participantsPerGame"],
                    "isReconnect": False,
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
        else:
            assert(self.isReconnect)

            # send joinGame request
            self.socket.sendMsg({
                "method": "reconnectGame",
                "pid": self.pid,
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
            

            msg = {
                "event": "serverConnected",
                "participantsCount": res["participantsCount"],
                "participantsPerGame": res["participantsPerGame"],
                "isReconnect": True,
            }

            self.qApp.put_nowait(msg)

            print("finished sending serverConnected event",msg)

        try:
            # repeatedly get event from our own queue
            event = await self.qGame.get()

            while event["event"] != "gameStart" and event["event"] != "gameInfo":
                if(event["event"] == "quitGame" or event["event"] == "appError"):
                    return
                elif(event["event"] == "gameError"):
                    # forward this event to app
                    print("forwarded to qApp")
                    self.qApp.put_nowait(event)
                    # then stop
                    return
                elif(event["event"] == "updateParticipantsCount"):
                    # forward this event to app
                    self.qApp.put_nowait(event)
                    event = await self.qGame.get()
                
                # do nothing otherwise, it could be events sent in the current round due to reconnection
            
            assert((self.isReconnect and event["event"] == "gameInfo") or (not(self.isReconnect) and event["event"]=="gameStart"))

            # Find our own info
            ps = event["participants"]
            p = list(filter(lambda p: p["id"]==self.pid,ps))[0]
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
                            "id": self.pid,
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
                p = list(filter(lambda p: p["id"]==self.pid,ps))[0]
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

    async def __getToken(self):
        async with httpx.AsyncClient() as client:
            timeout = httpx.Timeout(5.0, read=15.0)
            resp = await client.post(SERVER_URL + "/api/getToken", 
                timeout=timeout, 
                data={
                    "version": CLIENT_VERSION
                },
            )
            response = resp.json()
            if(response["result"]=="error"):
                raise Exception(response["errorMsg"])
            assert(response["result"]=="success")
            return None

    def __del__(self):
        if(hasattr(self,"socket")):
            # call destructor of the socket
            self.socket.stop()
        print("onlineGame destructor finished")