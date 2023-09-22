import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import (NumericProperty, ColorProperty, ListProperty)
from kivy.graphics import Color, Rectangle
from kivy.uix.popup import Popup

from widgets.NewRulesPopup import NewRulesPopup
from widgets.RulesPopup import RulesPopup
from widgets.WrapLabel import WrapLabel
from common.now import now

class GuessLabel(Label):
    border_color = ColorProperty((1, 1, 1, 1)) # Default border color (white)
    background_color = ColorProperty((0, 0, 0, 1)) # Default background color (black)

    def __init__(self, **kwargs):
        super(GuessLabel, self).__init__(**kwargs)
        self.changeColor("red")
        self.bind(size=self.update_canvas)
        self.bind(border_color=self.update_canvas)
        self.bind(background_color=self.update_canvas)

    def changeColor(self,color):
        if color == "red":
            self.background_color = (89.0/255,0,0,1)
        elif color == "green":
            self.background_color = (0,89.0/255,0,1)
        else: # black
            self.background_color = (0,0,0,1)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Border color
            Color(*self.border_color)
            # Border rectangle
            border_width = 4
            Rectangle(pos=self.pos, size=self.size)
            # Background color
            Color(*self.background_color)
            # Background rectangle (inside border)
            Rectangle(pos=(self.pos[0] + border_width, self.pos[1] + border_width),
                      size=(self.size[0] - 2 * border_width, self.size[1] - 2 * border_width))
            
class DigitButton(Button):
    digit = NumericProperty(0)

    def __init__(self, qApp, digit):
        super().__init__()
        self.digit = digit
        self.qApp = qApp
    
    def on_press(self):
        self.background_color = (1, 1, 1, 1) 
        self.color = (0, 0, 0, 1) 
        self.qApp.put_nowait({
            "event": "digitPressed",
            "digit": str(self.digit)
        })

    def on_release(self):
        self.background_color = (0, 0, 0, 1) 
        self.color = (1, 1, 1, 1)
        
    
# class CircularButton(ButtonBehavior, Label):
#     background_color = (0, 1, 0, 1)
#     background_down = (1, 0, 0, 1)
#     text = "hello world"

class GameScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp 
        self.app = App.get_running_app()

        numpad = self.ids["numpad"]

        for i in range(0,10): # [0..9]
            numpad.add_widget(DigitButton(self.qApp,i))
    
    def confirmPressed(self):
        self.qApp.put_nowait({
            "event": "confirmPressed"
        })

    def backspacePressed(self):
        self.qApp.put_nowait({
            "event": "backspacePressed"
        })

    def cancelPressed(self):
        self.qApp.put_nowait({
            "event": "cancelPressed"
        })

    def __addInfo(self,text,color=(1,1,1,1)):
        infoLayout = self.ids["infoLayout"]

        # A line copied from the kivy docs which is crucial
        infoLayout.bind(minimum_height=infoLayout.setter('height'))

        label = WrapLabel(
            text=text,
            color=color
        )

        infoLayout.add_widget(label)
        
    def __changeProposedGuess(self,guess, color="black",isClear=False):
        self.proposedGuess = guess
        
        guessLabel = self.ids["guessLabel"]
        guessLabel.changeColor(color)
        self.lastPressTime = now()
        
        if isClear and guess=="" and self.confirmedGuess != None:
            # Display the confirmedGuess instead if it exists, but internally the proposedGuess is empty
            guessLabel.changeColor("green")
            guessLabel.text = str(self.confirmedGuess)
        else:
            guessLabel.changeColor(color)
            guessLabel.text = guess
        

    def __submitGuess(self):
        timer = self.ids["timer"]

        guess = int(self.proposedGuess)
        assert(isinstance(guess, int) and guess <= 100 and guess >= 0)

        # pass to logic thread
        self.qGame.put_nowait({
            "event": "submitGuess",
            "guess": guess,
        })
        self.confirmedGuess = guess
        self.__changeProposedGuess("",isClear=True)

        self.__addInfo(
            f"Guess {guess} registered.",
            color=(0,1,0,1)
        )

        timer.color = (0,1,0,1)
        
    def on_pre_enter(self):
        print("game on_pre_enter")

        # Clear variables
        self.proposedGuess = ""
        self.confirmedGuess = None
        self.lastPressTime = None

        self.ids["guessLabel"].text = ""
        self.ids["guessLabel"].changeColor("red")
        
        # get gameInfo back from a previous screen
        gameInfo = self.app.globalGameInfo
        
        print(gameInfo)
        # make sure the game is still in progress
        assert(gameInfo["gameEnded"] == False)
        print("Game in progress")

        # make sure we are not dead
        isDead = gameInfo["us"]["isDead"] 
        assert(isDead == False)
        print("We are not dead")

        # assert round has started
        assert(gameInfo["roundStartTime"] <= now())
        print("Round has started")

        print("in game screen (after assertions)")
        
        # setup end time first, so that handleTimer works correctly
        self.endTime = gameInfo["roundEndTime"]

        # handle events
        self.handleGameTask = asyncio.create_task(self.__handleGame())

        # handle timer
        self.handleTimerTask = asyncio.create_task(self.__handleTimer())
    
    async def __handleTimer(self):
        try:
            timer = self.ids["timer"]
            guessLabel = self.ids["guessLabel"]
            infoLayout = self.ids["infoLayout"]
            problemTriggered = False
            fifteenSecondsTriggered = False

            timer.color = (1,1,1,1)

            while True: 
                if now() < self.endTime:
                    seconds = (self.endTime-now())//1000

                    # modify timer
                    if seconds < 60:
                        timer.text = f'{seconds}s'
                    else:
                        timer.text = f'{seconds//60}m{seconds%60}s'
                    
                    # modify color of guessLabel and give relevant infos
                    if seconds < 15 and self.confirmedGuess == None and self.proposedGuess == "":
                        guessLabel.changeColor("red")
                        timer.color = (1,0,0,1)
                        if not fifteenSecondsTriggered:
                            self.__addInfo(
                                "You have not make a guess. It will be a game over if you do not submit a guess before time is up.",
                                color=(1,0,0,1)
                            )
                        fifteenSecondsTriggered = True
                    elif seconds < 15 and self.confirmedGuess == None and self.proposedGuess != "":
                        if not fifteenSecondsTriggered:
                            self.__addInfo(
                                "Confirm button not pressed, we auto-submitted your guess as there is not much time left.",
                                color=(1,1,0,1)
                            )

                        self.__submitGuess()

                        fifteenSecondsTriggered = True
                    elif self.lastPressTime == None:
                        guessLabel.changeColor("red")
                    elif self.lastPressTime + 10*1000 < now() and self.confirmedGuess == None:
                        guessLabel.changeColor("red")
                        if not problemTriggered:
                            self.__addInfo(
                                "You need to press the tick button on the bottom right to register the guess.",
                                color=(1,0,0,1)
                            )
                        problemTriggered = True
                    elif self.lastPressTime + 10*1000 < now() and self.proposedGuess == "":
                        self.__changeProposedGuess("",isClear=True)
                    elif self.lastPressTime + 10*1000 < now() and self.confirmedGuess != int(self.proposedGuess):
                        self.__changeProposedGuess("",isClear=True)
                        if not problemTriggered:
                            self.__addInfo(
                                "Confirm button not pressed, we reverted your guess back to your last confirmed guess.",
                                color=(1,0,0,1)
                            )
                        problemTriggered = True
                    else:
                        # Reset problem triggered once there are no more problems 
                        problemTriggered = False
                elif now() >= self.endTime+5000: # -5s
                    # go back to home screen with a popup
                    if self.confirmedGuess == None:
                        popup = Popup(
                            title='GAME OVER', 
                            content=Label(text='You did not submit a guess in time. We brought you back to the home screen.'),
                            size_hint=(0.8, 0.3), 
                        )
                        popup.open()
                        
                    else:
                        popup = Popup(
                            title='Sorry an error occured', 
                            content=Label(text='We brought you back to the home screen.'),
                            size_hint=(0.8, 0.3), 
                        )
                        popup.open()
                        self.manager.current = "home"
                # Rember to await!
                await asyncio.sleep(1)
        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __handleTimer",repr(e))

    async def __handleGame(self):
        try:
            # get gameInfo back from a previous screen
            gameInfo = self.app.globalGameInfo
            self.aliveCount = gameInfo["aliveCount"]

            guessLabel = self.ids["guessLabel"]
            infoLayout = self.ids["infoLayout"]

            # only clear when it is the first round
            if gameInfo["round"] == 1:
                infoLayout.clear_widgets()

            self.__addInfo(f'Round {gameInfo["round"]}, you can make a guess between 0 and 100.')

            event = await self.qApp.get()
            print(event)
            while event["event"] != "gameInfo":
                if event["event"] == "digitPressed":
                    if int(self.proposedGuess + event["digit"]) <= 100 and int(self.proposedGuess + event["digit"]) >= 0:
                        self.__changeProposedGuess(str(int(self.proposedGuess + event["digit"])))# the str(int) is there to let us change from 0 to 4, lets say
                    else:
                        pass
                        # print(f'{int(guessLabel.text + event["digit"])} is not a valid guess')
                elif event["event"] == "confirmPressed":
                    if self.proposedGuess != "":
                        self.__submitGuess()

                elif event["event"] == "backspacePressed":
                    l = len(self.proposedGuess)
                    if l > 0:
                        self.__changeProposedGuess(self.proposedGuess[:-1])
                elif event["event"] == "cancelPressed":
                    self.__changeProposedGuess("")
                elif event["event"] == "participantDisconnectedMidgame":
                    # Print person died
                    ps = gameInfo["participants"]
                    p = list(filter(lambda p: p["id"]==event["id"],ps))[0]

                    if hasattr(self,"popup"):
                        self.popup.dismiss()
                    popup = NewRulesPopup(self.aliveCount,self.aliveCount-1,titleText=f'{p["nickname"]} disconnected midgame')
                    self.aliveCount -= 1
                    popup.open()
                    await asyncio.sleep(5)
                    popup.dismiss()
                else:
                    assert(event["event"] == "changeCountdown")
                    #! start time delay of the changeCountdown if participantDisconnectedMidgame is enforced by the 5-second popup window on the participantDisconnectedMidgame event. Will change that behaviour when we handle reconnection.
                    self.endTime = event["endTime"]+now()
                    if event["reason"] == "participantDisconnectedMidgame":
                        self.__addInfo(
                            "Based on the new rules, you now have 15 seconds to amend your guess.",
                            color=(1,1,0,1)
                        )
                    else:
                        assert(event["reason"] == "allDecided")
                        self.__addInfo(
                            "Every player has submitted their guess, the timer is changed to 15 seconds.",
                            color=(1,1,0,1)
                        )

                    
                    
                event = await self.qApp.get()
                print(event)

            assert(event["event"]=="gameInfo")
            self.app.globalGameInfo = event
            self.manager.current = "status"

        except Exception as e:
            # We need to print the exception or else it will fail silently
            popup = Popup(
                title='Sorry an error occured', 
                content=Label(text=''),
                size_hint=(0.8, 0.3), 
            )
            popup.open()
            print("ERROR __handleGame",repr(e))

    def on_pre_leave(self):
        if hasattr(self,"popup"):
            self.popup.dismiss()
        if hasattr(self,"handleTimerTask"):
            self.handleTimerTask.cancel()
        if hasattr(self,"handleGameTask"):
            self.handleGameTask.cancel()
    
    def showRules(self):
        self.popup = RulesPopup(detail=True,aliveCount=self.aliveCount)
        self.popup.open()
