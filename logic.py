import asyncio

# import from other project files
from game.onlineGame import OnlineGame

async def logic(qGame, qMain):
    '''This method is also run by the asyncio loop. A simple skeleton for hosting the game.
    '''

    try:
        while True:
            event = await qGame.get()

            # There might be some events/ responses left over after an error
            while(event["event"]!="modeSelection"):
                print(event)
                event = await qGame.get()
            
            # Clear qMain
            while(not qMain.empty()):
                await qMain.get()

            print(f'Mode selected: {event["mode"]}')

            game = None
            if event["mode"] == "online":
                print("Online mode selected")
                game = OnlineGame(qGame, qMain, event["nickname"])
            else:
                assert(event["mode"] == "solo")
                print("Solo mode selected")
                raise("solo mode not yet available")
            
            await game.play()
            
            #destruction
            del game
            
    except asyncio.CancelledError as e:
        print('Logic was canceled', e)
    finally:
        # when canceled, print that it finished
        print('Done logic')