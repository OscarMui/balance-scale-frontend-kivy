from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label

import re # regex
import asyncio

from widgets.RulesPopup import RulesPopup

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
        
        if(len(NICKNAME) > 12):
            popup = Popup(
                title='Error', 
                content=Label(text='Nickname cannot be longer than 12 characters.'),
                size_hint=(0.8, 0.3), # deactivate relative sizes
            )
            popup.open()
            return 
        
        regex = re.compile(r'^[A-Za-z0-9_]+$')
        if(regex.match(NICKNAME) == None):
            popup = Popup(
                title='Error', 
                content=Label(text='Nickname can only contain English letters, digits and underscores.'),
                size_hint=(0.8, 0.3), 
            )
            popup.open()
            return 
            
        if(mode=="solo"):
            popup = Popup(
                title='Coming soon', 
                content=None,
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
    
    def showRules(self):
        popup = RulesPopup(detail=True)
        popup.open()