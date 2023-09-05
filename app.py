import asyncio

from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from logic import logic

# Load static template
Builder.load_file("app.kv")

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

class TenbinApp(App):

    qGame = asyncio.Queue()
    qApp = asyncio.Queue()

    def build(self):
        # Create the manager
        sm = ScreenManager()
        
        # add screens
        sm.add_widget(HomeScreen(self.qGame,self.qApp,name='home'))
        sm.add_widget(SettingsScreen(self.qGame,self.qApp,name='settings'))

        # remember to return the screen manager
        return sm

    def app_func(self):
        '''This will run both methods asynchronously and then block until they
        are finished
        '''
        self.other_task = asyncio.ensure_future(logic(self.qGame,self.qApp))

        async def run_wrapper():
            # we don't actually need to set asyncio as the lib because it is
            # the default, but it doesn't hurt to be explicit
            await self.async_run(async_lib='asyncio')
            print('App done')
            self.other_task.cancel()

        return asyncio.gather(run_wrapper(), self.other_task)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TenbinApp().app_func())
    loop.close()