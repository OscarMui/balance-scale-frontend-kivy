import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

import os

from common.now import now
from common.visibility import show, hide
from widgets.RulesPopup import RulesPopup

class JoinRoomParticipantUI(BoxLayout):
    def __init__(self):
        super().__init__()

    def showPfp(self,isBot=False):
        if isBot:
            self.ids["pfp"].source = os.path.join("assets","bot.png")
        else:
            self.ids["pfp"].source = os.path.join("assets","pfp.jpg")
        show(self)

    def hidePfp(self):
        hide(self)

    def showNickname(self,nickname):
        if len(nickname) > 10:
            self.ids["nickname"].font_size = "12sp"
        else:
            self.ids["nickname"].font_size = "14sp"
        self.ids["nickname"].text = nickname
    

class JoinRoomScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp 
        self.app = App.get_running_app()

    def on_pre_enter(self):
        self.gameStarted = False
        joinRoomParticipantUIs = self.ids["joinRoomParticipantUIs"]
        joinRoomParticipantUIs.clear_widgets()

        titleLabel = self.ids["titleLabel"]
        bodyLabel = self.ids["bodyLabel"]
        titleLabel.text = "Connecting to server"
        bodyLabel.text = "Please wait..."

        self.ids["exitButton"].background_color = [1,0,0,1]
        self.joinRoomTask = asyncio.create_task(self.__joinRoom())
    
    async def __joinRoom(self):
        try:
            titleLabel = self.ids["titleLabel"]
            bodyLabel = self.ids["bodyLabel"]
            joinRoomParticipantUIs = self.ids["joinRoomParticipantUIs"]
            pus = [] # list of joinRoomParticipantUIs

            print("In join room")
            
            event = await self.qApp.get()
            print("joinRoom receives",event)
            if event["event"] == "serverConnected":
                participantCount = event["participantsCount"]
                participantsPerGame = event["participantsPerGame"]
                titleLabel.text = f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                bodyLabel.text = "The game will be filled with computer players if no one joins in 15 seconds. Please wait..."
                # Create that many participants
                for i in range(participantsPerGame):
                    pu = JoinRoomParticipantUI()
                    pus.append(pu)
                    joinRoomParticipantUIs.add_widget(pu)
                for i in range(participantCount):
                    pus[i].showPfp()
                for i in range(participantCount,participantsPerGame):
                    pus[i].hidePfp()
            else:
                assert(event["event"] == "serverConnectionFailed",'condition event["event"] == "serverConnectionFailed" not met')
                titleLabel.text = "An error occured"
                bodyLabel.text = event["errorMsg"]
                return
            
            event = await self.qApp.get()

            while event["event"] != "gameStart":
                if(event["event"] == "gameError"):
                    popup = Popup(
                        title='Sorry an error occured', 
                        content=Label(text=f'{event.get("errorMsg","")}\nWe brought you back to the home screen.'),
                        size_hint=(0.8, 0.3), 
                    )
                    popup.open()
                    self.manager.current = "home"
                else:    
                    assert(event["event"]=="updateParticipantsCount",'condition event["event"]=="updateParticipantsCount" not met')
                    participantCount = event["participantsCount"]
                    participantsPerGame = event["participantsPerGame"]
                    titleLabel.text = f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                    for i in range(participantCount):
                        pus[i].showPfp()
                    for i in range(participantCount,participantsPerGame):
                        pus[i].hidePfp()
                    event = await self.qApp.get()

            assert(event["event"]=="gameStart",'condition event["event"]=="gameStart" not met')
            print("gameStart event received by app")
            self.gameStarted = True
            gameInfo = event
            titleLabel.text = f'Game is starting ({len(gameInfo["participants"])}/{len(gameInfo["participants"])})'
            bodyLabel.text = "The game will start shortly"
            # print(self.ids["exitButton"].background_color)
            self.ids["exitButton"].background_color = [0.5,0.5,0.5, 1]
            # print(self.ids["exitButton"].background_color)
            for i in range(len(gameInfo["participants"])):
                p = gameInfo["participants"][i]
                pus[i].showNickname(p["nickname"])
                pus[i].showPfp(isBot=p["isBot"])

            if gameInfo["roundStartTime"]-now() > 0:
                print("Waiting for round start")
                await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)

            self.app.globalGameInfo = gameInfo
            self.manager.current = "game"

        except Exception as e:
            # 1. inform the onlineGame to stop
            self.qGame.put_nowait({
                "event": "appError"
            })
            # 2. inform the user by displaying the popup
            popup = Popup(
                title='Sorry an error occured', 
                content=Label(text='We brought you back to the home screen.'),
                size_hint=(0.8, 0.3), 
            )
            popup.open()
            # 3. go back to the home screen
            self.manager.current = "home"
            # 4. print the error We need to print the exception or else it will fail silently
            print("ERROR __joinRoom",repr(e))
    
    def exitGame(self):
        if(self.gameStarted):
            print("Game started cannot exit")
        else:
            print("quit game")
            self.qGame.put_nowait({
                "event": "quitGame"
            })
            self.joinRoomTask.cancel()
            self.manager.current = "home"
            return
    
    def on_pre_leave(self):
        if hasattr(self,"popup"):
            self.popup.dismiss()
        if hasattr(self,"joinRoomTask"):
            self.joinRoomTask.cancel()
    
    def showRules(self):
        self.popup = RulesPopup(detail=True)
        self.popup.open()