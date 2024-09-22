import asyncio

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
            while(event["event"]!="modeSelection" and event["event"]!="reconnectGame"):
                print("discard", event)
                event = await qGame.get()
            
            # Clear qMain
            while(not qApp.empty()):
                print("discard ",await qApp.get())

            game = None

            if(event["event"] == "modeSelection"):
                print(f'Mode selected: {event["mode"]}')
                if event["mode"] == "online":
                    print("Online mode selected")
                    game = OnlineGame(qGame, qApp, store, nickname=event["nickname"])
                else:
                    assert(event["mode"] == "solo")
                    print("Solo mode selected")
                    game = SoloGame(qGame, qApp, store, event["nickname"])
            else:
                assert(event["event"] == "reconnectGame")
                print("reconnect game")
                game = SoloGame(qGame, qApp, store, pid=event["pid"])
            await game.play()
            
            #destruction
            del game
            
    except asyncio.CancelledError as e:
        print('Logic was canceled', e)
    finally:
        # when canceled, print that it finished
        print('Done logic')