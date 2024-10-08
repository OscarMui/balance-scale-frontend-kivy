import asyncio
import os # for os.path.join
import random 
from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore

from views.GameScreen import GameScreen
from views.HomeScreen import HomeScreen
from views.JoinRoomScreen import JoinRoomScreen
from views.SettingsScreen import SettingsScreen
from views.StatusScreen import StatusScreen

from logic import logic

from common.constants import SCREEN_SIZE

# We need these imports in order for the .kv files to parse correctly
from widgets.ImageButton import ImageButton
from widgets.ImageButtonX import ImageButtonX
from widgets.WrapLabel import WrapLabel
from widgets.RulesPopup import RulesPopup
from widgets.NewRulesPopup import NewRulesPopup
from widgets.StatusPopup import StatusPopup

# Load static templates
Builder.load_file("main.kv")
Builder.load_file(os.path.join("views","HomeScreen.kv"))
Builder.load_file(os.path.join("views","GameScreen.kv"))
Builder.load_file(os.path.join("views","JoinRoomScreen.kv"))
Builder.load_file(os.path.join("views","SettingsScreen.kv"))
Builder.load_file(os.path.join("views","StatusScreen.kv"))
Builder.load_file(os.path.join("widgets","NewRulesPopup.kv"))
Builder.load_file(os.path.join("widgets","RulesPopup.kv"))
Builder.load_file(os.path.join("widgets","StatusPopup.kv"))
Builder.load_file(os.path.join("widgets","ImageButton.kv"))
Builder.load_file(os.path.join("widgets","ImageButtonX.kv"))
Builder.load_file(os.path.join("widgets","WrapLabel.kv"))
Builder.load_file(os.path.join("widgets","Announcement.kv"))

# Set default screen size to a landscape phone
if platform == 'android' or platform == "ios":
    Window.fullscreen = 'auto'
elif SCREEN_SIZE == "IPAD_LANDSCAPE":
    Window.size = (667, 512)
elif SCREEN_SIZE == "IPAD_PORTRAIT":
    Window.size = (512, 667)
else:
    Window.size = (667, 375)

class TenbinApp(App):

    qGame = asyncio.Queue()
    qApp = asyncio.Queue()
    globalNickname = None
    globalId = None
    globalGameInfo = None
    globalNews = None

    # INIT STORAGE
    store = JsonStore('v1.json')

    if not store.exists('nicknameV1'):
        NICKNAME = "Alice"+str(random.randint(1000,10000))
        store.put('nicknameV1', value=NICKNAME)

    def build(self):
        # Create the manager
        sm = ScreenManager(transition=FadeTransition())
        
        # add screens
        sm.add_widget(HomeScreen(self.qGame,self.qApp,self.store,name='home'))
        sm.add_widget(JoinRoomScreen(self.qGame,self.qApp,self.store,name='joinRoom'))
        sm.add_widget(GameScreen(self.qGame,self.qApp,self.store,name='game'))
        sm.add_widget(StatusScreen(self.qGame,self.qApp,self.store,name='status'))
        sm.add_widget(SettingsScreen(self.qGame,self.qApp,self.store,name='settings'))

        # remember to return the screen manager
        return sm

    def app_func(self):
        '''This will run both methods asynchronously and then block until they
        are finished
        '''
        self.other_task = asyncio.ensure_future(logic(self.qGame,self.qApp,self.store))

        async def run_wrapper():
            # we don't actually need to set asyncio as the lib because it is
            # the default, but it doesn't hurt to be explicit
            await self.async_run(async_lib='asyncio')
            print('App done')
            self.other_task.cancel()

        return asyncio.gather(run_wrapper(), self.other_task)

if __name__ == '__main__':
    # register our google font
    LabelBase.register(
        name='Noto Sans',
        fn_regular='fonts/Noto_Sans_TC/NotoSansTC-Regular.ttf',
        fn_bold='fonts/Noto_Sans_TC/NotoSansTC-Bold.ttf',
    )
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TenbinApp().app_func())
    loop.close()