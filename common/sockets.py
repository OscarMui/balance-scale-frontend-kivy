import asyncio
import json

# send a message to the websocket
def sendMsg(ws,msg):
    ws.send(json.dumps(msg))

# ws.recv() will stop the ping pongs
# receive a message, only use this when you know the message will not come soon
# async def recvMsg(ws):
#     return await asyncio.get_event_loop().run_in_executor(None, ws.recv)

# receive messages, then put all messages in an asyncio queue
async def recvMsgs(ws, queue):
    while True:
        msg = await asyncio.get_event_loop().run_in_executor(None, ws.recv)
        await queue.put(json.loads(msg))

# responsible for sending pings
async def pingpong(ws):
    while True:
        # print("ping")
        ws.ping()
        await asyncio.sleep(5)