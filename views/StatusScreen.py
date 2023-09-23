import asyncio
import os

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from common.now import now
from common.visibility import show,hide
from widgets.NewRulesPopup import NewRulesPopup
from widgets.RulesPopup import RulesPopup

class ParticipantUI(BoxLayout):

    def __init__(self,nickname,isBot):
        super().__init__()
        if len(nickname) > 10:
            self.ids["nickname"].font_size = "12sp"
        else:
            self.ids["nickname"].font_size = "14sp"
        self.ids["nickname"].text = nickname
        if isBot:
            self.ids["pfp"].source = os.path.join("assets","bot.png")
        else:
            self.ids["pfp"].source = os.path.join("assets","pfp.jpg")

    def declareWin(self):
        win = self.ids["win"]
        win.text = "WIN"
        win.font_size = "20sp"
        win.color = (0,1,1,1)
        show(win,animation=True)

    def declareGameOver(self,animation=True):
        win = self.ids["win"]
        win.text = "GAME OVER"
        win.font_size = "16sp"
        win.color = (1,0,0,1)
        show(win,animation=animation)    

    def changeInfoText(self,text):
        self.ids["info"].text = text

    def changeInfoColor(self,color):
        if color == "red":
            self.ids["info"].color = (1,0,0,1)
            # print("label color changed to red")
        else:
            # white
            self.ids["info"].color = (1,1,1,1)

class StatusScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp  
        self.app = App.get_running_app()
        self.scores = None
        self.isDeads = None

    def on_pre_enter(self):
        # reset UIs
        titleLabel = self.ids["titleLabel"]
        titleLabel.color = (1,1,1,1)

        infoLabel = self.ids["infoLabel"]
        # hide quit button
        hide(self.ids["exitButton"])
        infoLabel.pos_hint= {'center_x': 0.5, 'y': 0.07}

        self.statusTask = asyncio.create_task(self.__status())
    
    async def __status(self):
        try:
            # declare shorthands
            titleLabel = self.ids["titleLabel"]
            calculationLabel = self.ids["calculationLabel"]
            infoLabel = self.ids["infoLabel"]
            participantUIs = self.ids["participantUIs"]

            print("In status")
            
            gameInfo = self.app.globalGameInfo
            while True:
                # clear prev state
                participantUIs.clear_widgets()
                hide(calculationLabel)
                calculationLabel.text = ""
                calculationLabel.color=(1,1,1,1)
                titleLabel.text = "[ROUND OVER]"
                infoLabel.text = "The player that is closest to the target (average times 0.8) wins this round."
                infoLabel.color=(1,1,1,1)
                ps = gameInfo["participants"]

                pus = list(map(lambda p: {**p, "ui": ParticipantUI(p["nickname"],p["isBot"])},ps))
                
                # prepare prevScore - clear it if round == 2 (first time visiting this screen in a game)
                # for animation only, persists between rounds
                if gameInfo["round"] == 2:
                    self.scores = [0 for p in ps]
                    self.isDeads = [False for p in ps]

                # update the isDeads list at the start if it is disconnectedMidgame
                for d in gameInfo["justDiedParticipants"]:
                    if d["reason"]=="disconnectedMidgame":
                        for i in range(len(pus)):
                            if pus[i]["id"] == d["id"]:
                                self.isDeads[i] = True
                                print("found justDiedParticipantMidgame")

                guessSum = 0
                numGuesses = 0
                for i in range(len(pus)):
                    pu = pus[i]
                    guess = pu["guess"]

                    if self.isDeads[i]:
                        pu["ui"].declareGameOver(animation=False)
                    if guess != None:
                        numGuesses += 1
                        # Calculate sum
                        guessSum += guess

                        # Gradually prepare for the calculationLabel
                        pu["ui"].changeInfoText(str(guess))
                        if calculationLabel.text == "":
                            calculationLabel.text = "(" + str(guess)
                        else:
                            calculationLabel.text = calculationLabel.text + " + "  + str(guess)
                    participantUIs.add_widget(pu["ui"])

                # finish preparing calculationLabel
                average = round(guessSum/numGuesses,2)
                target = round(gameInfo["target"],2)
                calculationLabel.text = calculationLabel.text + f')/{numGuesses} = {average}\n{average} * 0.8 = {target}'
            
                await asyncio.sleep(1)

                # Show calculationLabel
                show(calculationLabel,animation=True)

                await asyncio.sleep(1)

                # Either 2 or 4 will be in justAppliedRules
                if 2 in gameInfo["justAppliedRules"]:
                    infoLabel.color = (0,1,1,1)
                    infoLabel.text = "Rule applied: If someone chooses 0, a player who chooses 100 wins the round."
                elif 4 in gameInfo["justAppliedRules"]:
                    infoLabel.color = (0,1,1,1)
                    infoLabel.text = "Rule applied: If two or more players choose the same number, the number is invalid and all players who selected the number will lose a point."
                
                for i in range(len(pus)):
                    pu = pus[i]
                    if pu["id"] in gameInfo["winners"]:
                        pu["ui"].declareWin()

                await asyncio.sleep(3)

                calculationLabel.text = ""
                infoLabel.color = (1,1,1,1)
                infoLabel.text = "All non-winners will have their scores deducted."
                for i in range(len(pus)):
                    pu = pus[i]
                    pu["ui"].changeInfoText(str(self.scores[i]))
                    if self.isDeads[i]:
                        pu["ui"].changeInfoColor("red")

                await asyncio.sleep(1)

                if 3 in gameInfo["justAppliedRules"]:
                    infoLabel.color = (0,1,1,1)
                    infoLabel.text = "Rule applied: If a player chooses the exact correct number, they win the round and all other players lose two points."

                for i in range(len(pus)):
                    pu = pus[i]
                    if pu["id"] not in gameInfo["winners"]:
                        pu["ui"].changeInfoColor("red")
                    pu["ui"].changeInfoText(str(pu["score"]))
                    self.scores[i] = pu["score"]
                    self.isDeads[i] = pu["isDead"]

                await asyncio.sleep(1)

                for d in gameInfo["justDiedParticipants"]:
                    pu = list(filter(lambda p: p["id"]==d["id"],pus))[0]
                    if d["reason"]=="deadLimit":
                        pu["ui"].declareGameOver()
                        calculationLabel.color = (1,0,0,1)
                        calculationLabel.text += f'{pu["nickname"]} reached -5 score, GAME OVER.\n'
                    elif d["reason"]=="disconnected":
                        pu["ui"].declareGameOver()
                        calculationLabel.color = (1,0,0,1)
                        calculationLabel.text += f'{pu["nickname"]} disconnected, GAME OVER.\n'

                # Display special stuff based on special events
                if gameInfo["us"]["isDead"]:
                    titleLabel.color = (1,0,0,1)
                    titleLabel.text = "You are dead :("

                    # show quit button
                    infoLabel.pos_hint= {'center_x': 0.45, 'y': 0.07}
                    show(self.ids["exitButton"],animation=True)

                if gameInfo["gameEnded"]:
                    infoLabel.text = "Game ended"
                    ps = gameInfo["participants"]
                    filteredP = list(filter(lambda p: not p["isDead"] and not p["isBot"],ps))
                    filteredBots = list(filter(lambda p: not p["isDead"] and p["isBot"],ps))
                    if(len(filteredP)==1):
                        p = filteredP[0]
                        titleLabel.color= (0,1,1,1)
                        titleLabel.text = f'The winner is {p["nickname"]}'
                    elif(len(filteredBots)>0):
                        # there are bots left
                        titleLabel.color= (0,1,1,1)
                        titleLabel.text = f'The winner are bots'
                    else:
                        titleLabel.color= (1,0,0,1)
                        infoLabel.text = f'GAME OVER for everyone'
                       
                    

                    # show quit button
                    show(self.ids["exitButton"],animation=True)
                    infoLabel.pos_hint= {'center_x': 0.45, 'y': 0.07}

                    # stop working
                    return
                
                # Determine what to do afterwards
                if gameInfo["us"]["isDead"]:
                    # Continue looping in the StatusScreen
                    infoLabel.text = "You are spectating, waiting for others to make their guesses. You can leave the game at any time."
                    
                    dpLen = len(list(filter(lambda dp : dp["reason"]!="disconnectedMidgame",gameInfo["justDiedParticipants"])))
                    if dpLen > 0:
                        await asyncio.sleep(3)
                        if hasattr(self,"popup"):
                            self.popup.dismiss()
                        popup = NewRulesPopup(dpLen + gameInfo["aliveCount"],gameInfo["aliveCount"],titleText="Someone died")
                        popup.open()
                        await asyncio.sleep(5)
                        popup.dismiss()
                    
                    event = await self.qApp.get()
                    assert(event["event"]=="gameInfo")
                    print(event)
                    gameInfo = event
                else:
                    dpLen = len(list(filter(lambda dp : dp["reason"]!="disconnectedMidgame",gameInfo["justDiedParticipants"])))
                    if dpLen > 0:
                        # Display the someone died popup until it is time
                        await asyncio.sleep(3)
                        if hasattr(self,"popup"):
                            self.popup.dismiss()
                        popup = NewRulesPopup(dpLen + gameInfo["aliveCount"],gameInfo["aliveCount"],titleText="Someone died")
                        popup.open()
                        if gameInfo["roundStartTime"]-now() > 0:
                            print("Waiting for round start while displaying the popup")
                            await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)
                        popup.dismiss()
                        self.manager.current = "game"
                    else:
                        # Move to the game screen when it is time
                        if gameInfo["roundStartTime"]-now() > 0:
                            print("Waiting for round start")
                            await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)

                        self.manager.current = "game"
                    return

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
            print("ERROR __status",repr(e))

    def exitGame(self):
        if hasattr(self,"statusTask"):
            self.statusTask.cancel()
        self.app.globalGameInfo = None
        self.manager.current = "home"
        
    
    def on_pre_leave(self):
        if hasattr(self,"popup"):
            self.popup.dismiss()
        if hasattr(self,"statusTask"):
            self.statusTask.cancel()
    
    def showRules(self):
        gameInfo = self.app.globalGameInfo
        self.popup = RulesPopup(detail=True,aliveCount=gameInfo["aliveCount"])
        self.popup.open()