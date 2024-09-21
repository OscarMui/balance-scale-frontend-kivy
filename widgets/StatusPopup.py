import os

from widgets.WrapLabel import WrapLabel
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from common.visibility import show

class StatusPopupParticipantUI(BoxLayout):
    def __init__(self,p,hasWon,isFirstRound):
        super().__init__()

        win = self.ids["win"]
        guessLabel = self.ids["guessLabel"]
        scoreLabel = self.ids["scoreLabel"]

        nickname = p["nickname"]
        isBot = p["isBot"]
        isDead = p["isDead"]
        guess = p.get("guess",None) # attr might not be provided if round number = 1
        score = p["score"]

        if len(nickname) > 11:
            self.ids["nickname"].font_size = "10sp"
        else:
            self.ids["nickname"].font_size = "12sp"
        self.ids["nickname"].text = nickname
        if isBot:
            self.ids["pfp"].source = os.path.join("assets","bot.png")
        else:
            self.ids["pfp"].source = os.path.join("assets","pfp.png")
        if isDead:
            win.text = "GAME OVER"
            win.font_size = "14sp"
            win.color = (1,0,0,1)
            show(win)
        if not isFirstRound:
            if hasWon:
                win.text = "WIN"
                win.font_size = "18sp"
                win.color = (0,1,1,1)
                show(win)
            else:
                scoreLabel.color = (1,0,0,1)
            if guess != None:
                guessLabel.text = str(guess)
            scoreLabel.text = str(score)

class StatusPopup(Popup):
    def __init__(self,gameInfo,**kwargs):
        super().__init__(**kwargs) 

        if gameInfo["round"]==1:
            self.title = "Players"
        else:
            self.title = "Previous Round"
        calculationLabel = self.ids["calculationLabel"]
        participantUIs = self.ids["participantUIs"]
        statusLayout = self.ids["statusLayout"]

        ps = gameInfo["participants"]
        numGuesses = 0
        guessSum = 0

        for i in range(len(ps)):
            p = ps[i]
            guess = p.get("guess",None) # attr might not be provided if round number = 1
            
            ui = StatusPopupParticipantUI(p,p["id"] in gameInfo.get("winners",[]),gameInfo["round"]==1)
            participantUIs.add_widget(ui)
                

            if guess != None:
                numGuesses += 1
                guessSum += guess
                if calculationLabel.text == "":
                    calculationLabel.text = "(" + str(guess)
                else:
                    calculationLabel.text = calculationLabel.text + " + "  + str(guess)

        if gameInfo["round"] != 1:
            # finish preparing calculationLabel
            average = round(guessSum/numGuesses,2)
            target = round(gameInfo["target"],2)
            calculationLabel.text = calculationLabel.text + f')/{numGuesses} = {average}\n{average} * 0.8 = {target}'

            justAppliedRulesLabel = WrapLabel(text="",color=(0,1,1,1),font_size="12sp")
            for r in gameInfo["justAppliedRules"]:
                if r == 2:
                    justAppliedRulesLabel.text += "Rule applied: If someone chooses 0, a player who chooses 100 wins the round.\n"
                if r == 3:
                    justAppliedRulesLabel.text += "Rule applied: If a player chooses the exact correct number, they win the round and all other players lose two points.\n"
                if r == 4:
                    justAppliedRulesLabel.text += "Rule applied: If two or more players choose the same number, the number is invalid and all players who selected the number will lose a point.\n"
            if len(gameInfo["justAppliedRules"])>0:
                statusLayout.add_widget(justAppliedRulesLabel)
                participantUIs.size_hint_y -= 0.15
                statusLayout.size_hint_y += 0.15

            justDiedParticipantsLabel = WrapLabel(text="",color=(1,0,0,1),font_size="12sp")
            for d in gameInfo["justDiedParticipants"]:
                p = list(filter(lambda p: p["id"]==d["id"],ps))[0]
                if d["reason"]=="deadLimit":
                    justDiedParticipantsLabel.text += f'{p["nickname"]} reached -5 score, GAME OVER.\n'
                elif d["reason"]=="disconnected":
                    justDiedParticipantsLabel.text += f'{p["nickname"]} disconnected, GAME OVER.\n'
                elif d["reason"]=="disconnectedMidgame":
                    justDiedParticipantsLabel.text += f'{p["nickname"]} disconnected midgame, GAME OVER.\n'
            if len(gameInfo["justDiedParticipants"])>0:
                statusLayout.add_widget(justDiedParticipantsLabel)
                participantUIs.size_hint_y -= 0.2
                statusLayout.size_hint_y += 0.2