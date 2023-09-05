import asyncio

# A simple skeleton for hosting the game, this function will be run in parallel with main.py. 
async def logic(qGame, qMain):
    '''This method is also run by the asyncio loop and periodically prints
    something.
    '''
    try:
        while True:
            event = await qGame.get()
            print(event)
            assert(event["event"]=="modeSelection")
            print(f'Mode selected: {event["mode"]}')

    except asyncio.CancelledError as e:
        print('Wasting time was canceled', e)
    finally:
        # when canceled, print that it finished
        print('Done wasting time')