import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from common.now import now
from common.visibility import show,hide

class ParticipantUI(BoxLayout):

    def __init__(self,nickname):
        super().__init__()
        if len(nickname) > 10:
            self.ids["nickname"].font_size = "12sp"
        else:
            self.ids["nickname"].font_size = "14sp"
        self.ids["nickname"].text = nickname

    def declareWin(self):
        win = self.ids["win"]
        win.text = "WIN"
        win.font_size = "20sp"
        win.color = (0,1,1,1)
        show(win,animation=True)

    def declareGameOver(self,animation=True):
        win = self.ids["win"]
        win.text = "GAME OVER"
        win.font_size = "18sp"
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

                pus = list(map(lambda p: {**p, "ui": ParticipantUI(p["nickname"])},ps))
                
                # prepare prevScore - clear it if round == 2 (first time visiting this screen in a game)
                # for animation only, persists between rounds
                if gameInfo["round"] == 2:
                    self.scores = [0 for p in ps]
                    self.isDeads = [False for p in ps]

                guessSum = 0
                for i in range(len(pus)):
                    pu = pus[i]
                    guess = pu["guess"]

                    if self.isDeads[i]:
                        pu["ui"].declareGameOver(animation=False)
                    if guess != None:
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
                numAlive = len(list(filter(lambda x: not x,self.isDeads)))
                average = round(guessSum/numAlive,2)
                target = round(gameInfo["target"],2)
                calculationLabel.text = calculationLabel.text + f')/{numAlive} = {average}\n{average} * 0.8 = {target}'
            
                await asyncio.sleep(1)

                # Show calculationLabel
                show(calculationLabel,animation=True)

                await asyncio.sleep(1)

                # Either 2 or 4 will be in justAppliedRules
                print(gameInfo["justAppliedRules"],2 in gameInfo["justAppliedRules"], 4 in gameInfo["justAppliedRules"])
                if 2 in gameInfo["justAppliedRules"]:
                    infoLabel.color = (0,1,1,0)
                    infoLabel.text = "Rule applied: If someone chooses 0, a player who chooses 100 automatically wins the round."
                elif 4 in gameInfo["justAppliedRules"]:
                    infoLabel.color = (0,1,1,0)
                    infoLabel.text = "Rule applied: If two or more players choose the same number, the number is invalid and all players who selected the number will lose a point."
                
                for i in range(len(pus)):
                    pu = pus[i]
                    if pu["id"] in gameInfo["winners"]:
                        pu["ui"].declareWin()

                await asyncio.sleep(3)

                infoLabel.color = (1,1,1,1)
                infoLabel.text = "All non-winners will have their scores deducted."
                for i in range(len(pus)):
                    pu = pus[i]
                    pu["ui"].changeInfoText(str(self.scores[i]))

                await asyncio.sleep(1)

                if 3 in gameInfo["justAppliedRules"]:
                    infoLabel.color = (0,1,1,0)
                    infoLabel.text = "Rule applied: If a player chooses the exact correct number, they win the round and all other players lose two points."

                for i in range(len(pus)):
                    pu = pus[i]
                    if pu["id"] not in gameInfo["winners"]:
                        pu["ui"].changeInfoColor("red")
                    pu["ui"].changeInfoText(str(pu["score"]))
                    self.scores[i] = pu["score"]

                await asyncio.sleep(1)

                for i in range(len(pus)):
                    pu = pus[i]
                    print(pu["isDead"])
                    if pu["isDead"]:
                        pu["ui"].declareGameOver()
                        self.isDeads[i] = True
                        calculationLabel.color = (1,0,0,1)
                        calculationLabel.text = "One or more players reached -5 score. GAME OVER for them."

                # Display special stuff based on special events
                if gameInfo["us"]["isDead"]:
                    titleLabel.color = (1,0,0,1)
                    titleLabel.text = "You are dead :("

                    # show quit button
                    infoLabel.pos_hint= {'center_x': 0.45, 'y': 0.07}
                    infoLabel.size_hint= (1, None)
                    show(self.ids["exitButton"],animation=True)

                if gameInfo["gameEnded"]:
                    infoLabel.text = "Game ended."

                    # show quit button
                    show(self.ids["exitButton"],animation=True)
                    infoLabel.pos_hint= {'center_x': 0.45, 'y': 0.07}
                    infoLabel.size_hint= (1, None)

                    # stop working
                    return
                
                # Determine what to do afterwards
                if gameInfo["us"]["isDead"]:
                    # Continue looping in the StatusScreen
                    infoLabel.text = "You are spectating, waiting for others to make their guesses. You can leave the game at any time."
                    event = await self.qApp.get()
                    assert(event["event"]=="gameInfo")
                    print(event)
                    gameInfo = event
                else:
                    # Move to the game screen when it is time
                    if gameInfo["roundStartTime"]-now() > 0:
                        print("Waiting for round start")
                        await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)

                    self.manager.current = "game"
                    return

        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __status",repr(e))

    def exitGame(self):
        self.app.globalGameInfo = None
        self.manager.current = "home"