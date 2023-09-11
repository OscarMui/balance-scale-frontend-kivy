import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout

from common.now import now
from common.visibility import show,hide

class ParticipantUI(BoxLayout):

    def __init__(self,nickname):
        super().__init__()
        self.ids["nickname"].text = nickname

    def declareWin(self):
        win = self.ids["win"]
        win.text = "WIN"
        show(win,animation=True)

    def declareGameOver(self):
        win = self.ids["win"]
        win.text = "GAME OVER"
        win.color = (1,0,0,1)
        show(win,animation=True)    

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
                titleLabel.text = "[ROUND OVER]"

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
                        pu["ui"].declareGameOver()
                    if guess != None:
                        # Calculate sum
                        guessSum += guess

                        # Gradually prepare for the calculationLabel
                        pu["ui"].changeInfoText(str(guess))
                        if i == 0:
                            calculationLabel.text = "(" + str(guess)
                        else:
                            calculationLabel.text = calculationLabel.text + " + "  + str(guess)
                    participantUIs.add_widget(pu["ui"])

                # finish preparing calculationLabel
                average = round(guessSum/len(pus),2)
                target = round(gameInfo["target"],2)
                calculationLabel.text = calculationLabel.text + f')/{len(pus)} = {average}\n{average} * 0.8 = {target}'
            
                await asyncio.sleep(1)

                # Show calculationLabel
                show(calculationLabel,animation=True)

                await asyncio.sleep(1)

                for i in range(len(pus)):
                    pu = pus[i]
                    if pu["id"] in gameInfo["winners"]:
                        pu["ui"].declareWin()

                await asyncio.sleep(2)

                for i in range(len(pus)):
                    pu = pus[i]
                    pu["ui"].changeInfoText(str(self.scores[i]))

                await asyncio.sleep(1)

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
                
                if gameInfo["gameEnded"]:
                    infoLabel.text = "Game ended."
                    # show quit button
                    show(self.ids["exitButton"],animation=True)
                    return

                if gameInfo["us"]["isDead"]:
                    titleLabel.text = "You are dead :("
                    infoLabel.text = "You are spectating, waiting for others to make their guesses. You can leave the game at any time."
                    
                    # show quit button
                    show(self.ids["exitButton"],animation=True)

                    event = await self.qApp.get()
                    assert(event["event"]=="gameInfo")
                    gameInfo = event
                else:
                    if gameInfo["roundStartTime"]-now() > 0:
                        print("Waiting for round start")
                        await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)

                    self.manager.current = "game"
                    return

        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __status",str(e))

    def exitGame(self):
        self.app.globalGameInfo = None
        self.manager.current = "home"