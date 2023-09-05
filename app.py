import asyncio

from kivy.app import App
from kivy.lang.builder import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from logic import logic

# Load static template
Builder.load_file("app.kv")

class HomeScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp
        self.app = App.get_running_app()

    def modeSelection(self, mode):
        NICKNAME = self.ids["nickname"].text

        # TODO: Disallow any symbols

        if(NICKNAME==""):
            popup = Popup(
                title='Error', 
                content=Label(text='Nickname cannot be blank'),
                size_hint=(None, None), # deactivate relative sizes
                size = (500,300)
            )
            popup.open()
            return 
        
        if(mode=="solo"):
            popup = Popup(
                title='Coming soon', 
                content=None,
                size_hint=(None, None), # deactivate relative sizes
                size = (500,300)
            )
            popup.open()
            return

        print(f'HomeScreen.playGame text: {NICKNAME}, mode {mode}')
        # put_nowait can be used because our queue does not have an upper limit
        
        self.app.globalNickname = NICKNAME

        self.qGame.put_nowait({
            "event": "modeSelection",
            "mode": mode,
            "nickname": NICKNAME,
        })

        self.manager.current = "joinRoom"
        
class JoinRoomScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp  

    def on_enter(self):
        self.joinRoomTask = asyncio.create_task(self.__joinRoom())
    
    async def __joinRoom(self):
        titleLabel = self.ids["titleLabel"]
        bodyLabel = self.ids["bodyLabel"]

        print("In join room")

        event = await self.qApp.get()

        while event["event"] != "gameStart":
            if event["event"] == "serverConnected":
                titleLabel.text = "Waiting for participants to join"
            elif event["event"] == "serverConnectionFailed":
                titleLabel.text = "An error occured"
                bodyLabel.text = event["errorMsg"]
            event = await self.qApp.get()

class SettingsScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp  

class TenbinApp(App):

    qGame = asyncio.Queue()
    qApp = asyncio.Queue()
    globalNickname = None

    def build(self):
        # Create the manager
        sm = ScreenManager()
        
        # add screens
        sm.add_widget(HomeScreen(self.qGame,self.qApp,name='home'))
        sm.add_widget(JoinRoomScreen(self.qGame,self.qApp,name='joinRoom'))
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