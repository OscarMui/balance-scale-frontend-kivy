import webbrowser

from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.button import Button

from widgets.WrapLabel import WrapLabel
from widgets.ImageButton import ImageButton
from common.constants import DISCORD_URL
from common.visibility import hide

class LeftWrapLabel(WrapLabel):
    pass

# A very specific class that does what we want to achieve in this popup
class ShowAnswerButton(ImageButton):
    def __init__(self,layout,ans,**kwargs):
        super(ShowAnswerButton,self).__init__(**kwargs)
        self.ans = ans
        self.layout = layout
        
    def showAns(self):
        print("showAns")
        # Find our index
        i = 0
        while i < len(self.layout.children) and self.layout.children[i] != self:
            i += 1
        self.layout.remove_widget(self)

        # insert the answer back at the same index
        self.layout.add_widget(LeftWrapLabel(
            text = self.ans
        ),i)
        
class RulesPopup(Popup):
    qs = [
        {
            "question": "Q: I am confused after reading the rules.",
            "answer": "A: You are not alone! The key to the game is that 0.8 multiplier. With that, it means that the target will never be above 80, as the average is at most 100. Then people should never choose a number above 80 to win. But if everyone thinks the same, they should not choose a number above 64, as the average will not go beyond 80. This creates a dilemma that leads to people choosing smaller and smaller numbers.",
        },
        {
            "question": "Q: I watched Alice in Borderland, are there any differences between your game and the game in the TV show?",
            "answer": "A: Not much except for a few technicalities, and the fact that you don't die if you lose. This game is designed to recreate the game in Alice in Borderland, so that viewers can try it out for themselves. \nHere are the differences:\n1. The round time is shortened to 1 minute. \n2. The GAME OVER score is changed to -5.\n3. Players can disconnect anytime, it counts as a GAME OVER for that player.\n4. Players need to type in the number digit by digit.\nThe changes are mainly to address the fast lifestyle of people outside of the Borderland, and the fact that your screen is smaller than the one the TV show uses.",
        },
        {
            "question": "Q: Am I allowed to communicate?",
            "answer": "A: Absolutely. That's what makes the game interesting. It is a shame that I do not have time to add communication features in-game. You are encouraged to communicate with your opponents during the game using other means.",
        },
        {
            "question":"Q: How do computer players behave?",
            "answer": "A: Computer players will fill the game if there are no new joiners for 15 seconds. Or else I think there will never be a successful game being held.\nFor the math nerds, they will choose a number at random (uniformly) between 0 and 100*0.8^(round-1).\nIn other words, they would choose a number between 0 and 100 in the first round, then between 0 and 80, then between 0 and 64. I hope you get the idea.\nWhen there are two players left the computer player would choose a number among 0, 1, and 100.",
        }
    ]
    answersShown = [False for i in range(len(qs))]

    def __init__(self,detail=False,activeCount=None, **kwargs):
        super(RulesPopup, self).__init__(**kwargs)
        
        rulesLayout = self.ids["rulesLayout"]
        rulesLayout.bind(minimum_height=rulesLayout.setter('height'))

        # Add some spacing
        rulesLayout.add_widget(Label(
            text = "",
        ))
        
        if activeCount != None:
            if activeCount <= 4:
                rulesLayout.add_widget(WrapLabel(
                    text = "New rules upon elimination",
                    bold = True,
                ))
                rulesLayout.add_widget(LeftWrapLabel(
                    text = "1. If two or more players choose the same number, the number is invalid and all players who selected the number will lose a point.",
                ))
            if activeCount <= 3:
                rulesLayout.add_widget(LeftWrapLabel(
                    text = "2. If a player chooses the exact correct number, they win the round and all other players lose two points.",
                ))
            if activeCount <= 2:
                rulesLayout.add_widget(LeftWrapLabel(
                    text = "3. If someone chooses 0, a player who chooses 100 wins the round.",
                ))
        
        # General rules
        rulesLayout.add_widget(WrapLabel(
            text = "General Rules",
            bold = True,
        ))
        rulesLayout.add_widget(LeftWrapLabel(
            text = "Every player chooses a number between 0 and 100 in each round. The player closest to the target, that is the average of the numbers multiplied by 0.8, wins the round.",
        ))
        rulesLayout.add_widget(LeftWrapLabel(
            text = "All players start with 0 points. If a player reaches -5 points, it is a GAME OVER for that player. The last person standing wins.",
        ))
        rulesLayout.add_widget(LeftWrapLabel(
            text = "A new rule will be introduced for every player eliminated.",
        ))

        rulesLayout.add_widget(WrapLabel(
            text = "FAQs",
            bold = True,
        ))
        for i in range(len(self.qs)):
            q = self.qs[i]
            rulesLayout.add_widget(LeftWrapLabel(
                text = q["question"],
            ))
            rulesLayout.add_widget(ShowAnswerButton(rulesLayout,q["answer"]))

        rulesLayout.add_widget(LeftWrapLabel(
            text = "Created by KidProf\nFrontend: Python, Kivy, asyncio\nBackend: ExpressJS, Websockets"
        ))

        if detail:
            rulesLayout.add_widget(ImageButton(
                text = "Join Discord",
                color = (114.0/255,137.0/255,218.0/255,1),
                size_hint = (1, None),
                height = 100,
                background_color = (0,0,0,0),
                on_press = self.openDiscord,  
            ))

    def openDiscord(self,arg):
        webbrowser.open(DISCORD_URL)
        