from kivy.uix.screenmanager import Screen

class SettingsScreen(Screen):
    def __init__(self, qGame, qApp, store, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp  