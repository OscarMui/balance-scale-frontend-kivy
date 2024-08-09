import webbrowser
import re # regex

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from common.constants import DISCORD_URL
from widgets.RulesPopup import RulesPopup
from widgets.WrapLabel import WrapLabel

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

        if(NICKNAME==""):
            popup = Popup(
                title='Nickname Error', 
                content=WrapLabel(text='Nickname cannot be blank',pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3),
            )
            popup.open()
            return 
        
        if(len(NICKNAME) > 12):
            popup = Popup(
                title='Nickname Error', 
                content=WrapLabel(text='Nickname cannot be longer than 12 characters.',pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3), 
            )
            popup.open()
            return 
        
        regex = re.compile(r'^[A-Za-z0-9_]+$')
        if(regex.match(NICKNAME) == None):
            popup = Popup(
                title='Nickname Error', 
                content=WrapLabel(text='Nickname can only contain English letters, digits and underscores.',pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3), 
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
    
    def on_pre_leave(self):
        if hasattr(self,"popup"):
            self.popup.dismiss()
    
    def showRules(self):
        self.popup = RulesPopup(detail=True)
        self.popup.open()

    def openDiscord(self):
        webbrowser.open(DISCORD_URL)