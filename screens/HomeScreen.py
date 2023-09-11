from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.label import Label


class HomeScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp
        self.app = App.get_running_app()

    def on_pre_enter(self):
        pass

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