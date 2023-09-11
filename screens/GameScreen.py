import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import (NumericProperty, ColorProperty, ListProperty)
from kivy.graphics import Color, Rectangle

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
            self.background_color = (89.0/255,0,0,5)
        elif color == "green":
            self.background_color = (0,89.0/255,0,5)
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
        

    def on_pre_enter(self):
        print("game on_pre_enter")

        # Clear variables
        self.proposedGuess = ""
        self.confirmedGuess = None
        self.lastPressTime = None
        self.infos = ListProperty([]) 

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
            while True: 
                if now() < self.endTime:
                    seconds = (self.endTime-now())//1000

                    # modify timer
                    if seconds < 60:
                        timer.text = f'{seconds}s'
                    else:
                        timer.text = f'{seconds//60}m{seconds%60}s'
                    
                    # modify color of guessLabel
                    if self.lastPressTime == None:
                        guessLabel.changeColor("red")
                    elif self.lastPressTime + 10*1000 < now() and self.confirmedGuess == None:
                        guessLabel.changeColor("red")
                    elif self.lastPressTime + 10*1000 < now() and (self.proposedGuess == "" or self.confirmedGuess != int(self.proposedGuess)):
                        self.__changeProposedGuess("",isClear=True)

                # Rember to await!
                await asyncio.sleep(1)
        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __handleTimer",str(e))

    async def __handleGame(self):
        try:
            # get gameInfo back from a previous screen
            gameInfo = self.app.globalGameInfo

            guessLabel = self.ids["guessLabel"]

            event = await self.qApp.get()

            while event["event"] != "gameInfo":
                print(event)
                if event["event"] == "digitPressed":
                    if int(self.proposedGuess + event["digit"]) <= 100 and int(self.proposedGuess + event["digit"]) >= 0:
                        self.__changeProposedGuess(str(int(self.proposedGuess + event["digit"])))# the str(int) is there to let us change from 0 to 4, lets say
                    else:
                        pass
                        # print(f'{int(guessLabel.text + event["digit"])} is not a valid guess')
                elif event["event"] == "confirmPressed":
                    guess = int(self.proposedGuess)
                    assert(isinstance(guess, int) and guess <= 100 and guess >= 0)

                    # pass to logic thread
                    self.qGame.put_nowait({
                        "event": "submitGuess",
                        "guess": guess,
                    })
                    self.confirmedGuess = guess
                    self.__changeProposedGuess("",isClear=True)

                elif event["event"] == "backspacePressed":
                    l = len(self.proposedGuess)
                    if l > 0:
                        self.__changeProposedGuess(self.proposedGuess[:-1])
                elif event["event"] == "cancelPressed":
                    self.__changeProposedGuess("")
                else:
                    assert(event["event"] == "changeCountdown")
                    self.endTime = event["endTime"]
                    

                event = await self.qApp.get()

            assert(event["event"]=="gameInfo")
            self.app.globalGameInfo = event
            self.manager.current = "status"

        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __handleGame",str(e))

    def on_leave(self):
        if hasattr(self,"handleTimerTask"):
            self.handleTimerTask.cancel()
