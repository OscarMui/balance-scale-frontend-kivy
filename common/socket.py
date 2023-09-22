import asyncio
import json
import websocket
import ssl

class Socket:
    # A websocket connection, it has a public method for sending messages, and it will put all messages recevied in the specified queue
    
    def __init__(self,url,queue):
        # establish connection
        self.ws = websocket.create_connection(url,sslopt={"cert_reqs": ssl.CERT_NONE})
        self.queue = queue
        self.isOpen = True
        # spawns off ping pong task
        self.pingPongTask = asyncio.create_task(self.pingpong())
    
        # spawns off a task to put all msgs received in an event queue
        self.recvMsgsTask = asyncio.create_task(self.__recvMsgs())

    # send a message to the websocket
    def sendMsg(self,msg):
        self.ws.send(json.dumps(msg))

    # receive messages, then put all messages in an asyncio queue
    async def __recvMsgs(self):
        try:
            while True:
                msg = await asyncio.get_event_loop().run_in_executor(None, self.ws.recv)
                await self.queue.put(json.loads(msg))
        except Exception as e:
            print("exception in __recvMsgs",repr(e))
            if self.isOpen:
                self.queue.put_nowait({
                    "event": "gameError",
                    "errorMsg": "Network connection error."
                })
                self.stop()
            self.isOpen = False

    # responsible for sending pings
    async def pingpong(self):
        try:
            while True:
                self.ws.ping()
                await asyncio.sleep(5)
        except Exception as e:
            print("exception in pingPong",repr(e))
            if self.isOpen:
                self.queue.put_nowait({
                    "event": "gameError",
                    "errorMsg": "Network connection error."
                })
                self.stop()
            self.isOpen = False
    
    def stop(self):
        print("socket destructor called")
        if hasattr(self,"pingPongTask"):
            self.pingPongTask.cancel()
        if hasattr(self,"recvMsgsTask"):
            self.recvMsgsTask.cancel()  
        if hasattr(self,"ws"):
            self.ws.close()
        print("socket destructor finished")

    # def __del__(self):
    #     self.stop()
