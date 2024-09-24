import asyncio
import httpx

from common.constants import SERVER_URL

# import from other project files
from game.onlineGame import OnlineGame
from game.soloGame import SoloGame

async def logic(qGame, qApp, store):
    '''This method is also run by the asyncio loop. A simple skeleton for hosting the game.
    '''

    try:
        while True:
            event = await qGame.get()

            # There might be some events/ responses left over after an error
            while(event["event"]!="modeSelection"):
                print("discard", event)
                event = await qGame.get()
            
            # Clear qMain
            while(not qApp.empty()):
                print("discard ",await qApp.get())

            game = None

            print(f'Mode selected: {event["mode"]}')
            if event["mode"] == "online":
                print("Online mode selected")
                if store.exists('pidV1') and not store.get('pidV1')["value"] == None:
                    pid = store.get('pidV1')["value"]
                    async with httpx.AsyncClient() as client:
                        timeout = httpx.Timeout(5.0, read=15.0)
                        resp = await client.post(SERVER_URL + "/api/gamesStatus", 
                            timeout=timeout, 
                            data={
                                "pid": pid,
                            },
                        )
                        response = resp.json()
                        if(response["result"]=="error"):
                            raise Exception(response["errorMsg"])
                        assert(response["result"]=="success")
                        if(response["canReconnect"]):
                            game = OnlineGame(qGame, qApp, store, pid=pid)
                        else:
                            game = OnlineGame(qGame, qApp, store, nickname=event["nickname"])
                        print('Game status check completed')
                else:
                    game = OnlineGame(qGame, qApp, store, nickname=event["nickname"])
            else:
                assert(event["mode"] == "solo")
                print("Solo mode selected")
                game = SoloGame(qGame, qApp, store, event["nickname"])
            await game.play()
            
            #destruction
            del game
            
    except asyncio.CancelledError as e:
        print('Logic was canceled', e)
    finally:
        # when canceled, print that it finished
        print('Done logic')