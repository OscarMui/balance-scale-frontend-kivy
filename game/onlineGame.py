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
    endTime = 0
    startTime = 0
    # endTimeLock = asyncio.Lock()

    guess = None

    id = ""
    isDead = False
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
            assert(res["result"]=="success")

            print("Joined websocket")

        except Exception as e:
            print("Exception",e)
            await self.qApp.put({
                "event": "serverConnectionFailed",
                "errorMsg": str(e)
            })
            return
    
        await self.qApp.put({
            "event": "serverConnected"
        })

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
        if self.pingPongTask:
            self.pingPongTask.cancel()
        if self.recvMsgsTask:
            self.recvMsgsTask.cancel()  
        if self.ws:
            self.ws.close()
        print("onlineGame destructor finished")