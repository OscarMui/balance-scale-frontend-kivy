import asyncio
import random

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
            self.ids["pfp"].source = os.path.join("assets","pfp.png")
        show(self)

    def hidePfp(self):
        hide(self)

    def showNickname(self,nickname):
        if len(nickname) > 11:
            self.ids["nickname"].font_size = "12sp"
        else:
            self.ids["nickname"].font_size = "14sp"
        self.ids["nickname"].text = nickname
    

class JoinRoomScreen(Screen):
    def __init__(self, qGame, qApp, store, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp 
        self.endTime = 0
        self.store = store
        self.app = App.get_running_app()

    def on_pre_enter(self):
        self.gameStarted = False
        self.isReconnect = False
        joinRoomParticipantUIs = self.ids["joinRoomParticipantUIs"]
        joinRoomParticipantUIs.clear_widgets()

        titleLabel = self.ids["titleLabel"]
        bodyLabel = self.ids["bodyLabel"]
        titleLabel.text = "Connecting to server"
        bodyLabel.text = "Please wait..."

        self.ids["exitButton"].background_color = [1,0,0,1]
        self.joinRoomTask = asyncio.create_task(self.__joinRoom())
        self.handleTimerTask = asyncio.create_task(self.__handleTimer())

    async def __handleTimer(self):
        try:
            timer = self.ids["timer"]
            timerImage = self.ids["timerImage"]
            tipLabel = self.ids["tipLabel"]

            timer.color = (1,1,1,1)

            TIPS = self.app.globalNews["tips"] if self.app.globalNews != None else []
            # print(TIPS)
            if len(TIPS) > 0:
                show(tipLabel)
                tipLabel.text = "Tip:\n" + TIPS[random.randrange(0,len(TIPS))]
            else:
                hide(tipLabel)

            while True: 
                if now() < self.endTime:
                    show(timer)
                    show(timerImage)
                    if len(TIPS) > 0:
                        show(tipLabel)

                    seconds = (self.endTime-now())//1000

                    # modify timer
                    if seconds < 60:
                        timer.text = f'{seconds}s'
                    else:
                        timer.text = f'{seconds//60}m{seconds%60}s'
                    
                    # precisely change the tip when there is 7s left, just a random point s.t. it ensures tip changes from time to time
                    if seconds == 7 and len(TIPS) > 0:
                        tipLabel.text = "Tip:\n" + TIPS[random.randrange(0,len(TIPS))]
                else:
                    # A time in the past/ not initialised yet (it was initialised to 0, which is definitely smaller than now())
                    timer.text = ""
                    hide(timer)
                    hide(timerImage)
                    hide(tipLabel)
                    
                # Rember to await!
                await asyncio.sleep(1)
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
            print("ERROR __handleTimer",repr(e))

    
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
                self.isReconnect =  event["isReconnect"]
                participantCount = event["participantsCount"]
                participantsPerGame = event["participantsPerGame"]
                titleLabel.text = 'Reconnection successful to server' if event["isReconnect"] else f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                bodyLabel.text = 'You will be able to rejoin when the next round starts.' if event["isReconnect"] else "The game will be filled with computer players if no one joins in 15 seconds. Please wait..."

                # Create that many participants
                for i in range(participantsPerGame):
                    pu = JoinRoomParticipantUI()
                    pus.append(pu)
                    joinRoomParticipantUIs.add_widget(pu)
                for i in range(participantCount):
                    pus[i].showPfp()
                for i in range(participantCount,participantsPerGame):
                    pus[i].hidePfp()
                self.endTime = now() + (60*1000 if event["isReconnect"] else 15*1000)
            else:
                assert(event["event"] == "serverConnectionFailed",'condition event["event"] == "serverConnectionFailed" not met')
                titleLabel.text = "An error occured"
                bodyLabel.text = event["errorMsg"]
                return
            
            if event["isReconnect"]:
                event = await self.qApp.get()
                print("joinRoom receives",event)
                assert(event["event"]=="gameInfo",'condition event["event"]=="gameInfo" not met')
                self.app.globalGameInfo = event
                self.manager.current = "status"
                return 
            
            event = await self.qApp.get()

            while event["event"] != "gameStart":
                print("joinRoom receives",event)
                if(event["event"] == "gameError"):
                    popup = Popup(
                        title='Sorry an error occured', 
                        content=Label(text=f'{event.get("errorMsg","")}\nWe brought you back to the home screen.'),
                        size_hint=(0.8, 0.3), 
                    )
                    popup.open()
                    self.manager.current = "home"
                    return
                else:    
                    assert(event["event"]=="updateParticipantsCount",'condition event["event"]=="updateParticipantsCount" not met')
                    participantCount = event["participantsCount"]
                    participantsPerGame = event["participantsPerGame"]
                    titleLabel.text = f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                    for i in range(participantCount):
                        pus[i].showPfp()
                    for i in range(participantCount,participantsPerGame):
                        pus[i].hidePfp()
                    self.endTime = now() + 15*1000
                    event = await self.qApp.get()

            assert(event["event"]=="gameStart",'condition event["event"]=="gameStart" not met')
            self.endTime = 0 # the timer task will then hide the timer
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

            # TODO: Popup confirmation if it is a reconnection case
            if self.isReconnect:
                pass
            self.store.delete('pidV1')

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
        if hasattr(self,"handleTimerTask"):
            self.handleTimerTask.cancel()
    
    def showRules(self):
        self.popup = RulesPopup(detail=False)
        self.popup.open()