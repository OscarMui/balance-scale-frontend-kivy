'''Example shows the recommended way of how to run Kivy with the Python built
in asyncio event loop as just another async coroutine.
'''
import asyncio

from kivy.app import async_runTouchApp
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from logic import logic

kv = '''
BoxLayout:
    orientation: 'vertical'
    Button:
        id: btn
        text: 'Press me'
    BoxLayout:
        Label:
            id: label
            text: 'Button is "{}"'.format(btn.state)
'''

Builder.load_file("main.kv")

class HomeScreen(Screen):

    def __init__(self, qGame, qMain, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qMain = qMain  

    def modeSelection(self, mode):
        print(f'HomeScreen.playGame text: {self.ids["nickname"].text}, mode {mode}')
        # put_nowait can be used because our queue does not have an upper limit
        self.qGame.put_nowait({
            "event": "modeSelection",
            "mode": mode,
            "nickname": self.ids["nickname"].text,
        })

class SettingsScreen(Screen):
    qGame = None
    qMain = None
    
    def __init__(self, qGame, qMain, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qMain = qMain  

async def run_app_happily(root, other_task):
    '''This method, which runs Kivy, is run by the asyncio loop as one of the
    coroutines.
    '''

    # we don't actually need to set asyncio as the lib because it is the
    # default, but it doesn't hurt to be explicit
    await async_runTouchApp(root, async_lib='asyncio')  # run Kivy
    print('App done')
    # now cancel all the other tasks that may be running
    other_task.cancel()


async def waste_time_freely():
    '''This method is also run by the asyncio loop and periodically prints
    something.
    '''
    try:
        while True:
            print('Sitting on the beach')
            await asyncio.sleep(2)
    except asyncio.CancelledError as e:
        print('Wasting time was canceled', e)
    finally:
        # when canceled, print that it finished
        print('Done wasting time')

if __name__ == '__main__':
    def root_func():
        '''This will run both methods asynchronously and then block until they
        are finished
        '''

        # root = Builder.load_string(kv)  # root widget
        # other_task = asyncio.ensure_future(waste_time_freely())

        # queue of tasks from UIs to the logic
        qGame = asyncio.Queue()

        # queue of tasks from the logic to the UIs
        qMain = asyncio.Queue()

        # Create the manager
        sm = ScreenManager()

        sm.add_widget(HomeScreen(qGame,qMain,name='home'))
        sm.add_widget(SettingsScreen(qGame,qMain,name='settings'))

        other_task = asyncio.ensure_future(logic(qGame,qMain))
        return asyncio.gather(run_app_happily(sm, other_task), other_task)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(root_func())
    loop.close()