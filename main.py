import asyncio

from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.core.text import LabelBase

from screens.GameScreen import GameScreen
from screens.HomeScreen import HomeScreen
from screens.JoinRoomScreen import JoinRoomScreen
from screens.SettingsScreen import SettingsScreen
from screens.StatusScreen import StatusScreen

from common.now import now
from common.visibility import show, hide
from logic import logic

# Load static template
Builder.load_file("main.kv")

# Set default screen size to a landscape phone
Window.size = (667, 375)

class TenbinApp(App):

    qGame = asyncio.Queue()
    qApp = asyncio.Queue()
    globalNickname = None
    globalId = None
    globalGameInfo = None

    def build(self):
        # Create the manager
        sm = ScreenManager(transition=FadeTransition())
        
        # add screens
        sm.add_widget(HomeScreen(self.qGame,self.qApp,name='home'))
        sm.add_widget(JoinRoomScreen(self.qGame,self.qApp,name='joinRoom'))
        sm.add_widget(GameScreen(self.qGame,self.qApp,name='game'))
        sm.add_widget(StatusScreen(self.qGame,self.qApp,name='status'))
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
    # register our google font
    LabelBase.register(name='Noto Sans',
                      fn_regular='fonts/Noto_Sans_TC/static/NotoSansTC-Regular.ttf')
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TenbinApp().app_func())
    loop.close()