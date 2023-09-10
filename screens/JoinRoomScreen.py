import asyncio

from kivy.app import App
from kivy.uix.screenmanager import Screen

from common.now import now
from common.visibility import show, hide

class JoinRoomScreen(Screen):
    def __init__(self, qGame, qApp, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp 
        self.gameStarted = False
        self.app = App.get_running_app()

    def on_enter(self):
        self.joinRoomTask = asyncio.create_task(self.__joinRoom())
    
    async def __joinRoom(self):
        try:
            titleLabel = self.ids["titleLabel"]
            bodyLabel = self.ids["bodyLabel"]

            print("In join room")

            event = await self.qApp.get()

            while event["event"] != "gameStart":
                if event["event"] == "serverConnected":
                    participantCount = event["participantsCount"]
                    participantsPerGame = event["participantsPerGame"]
                    titleLabel.text = f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                    for i in range(min(5,event["participantsCount"])):
                        show(self.ids[f'pfp{i}'])
                elif event["event"] == "serverConnectionFailed":
                    titleLabel.text = "An error occured"
                    bodyLabel.text = event["errorMsg"]
                    return
                else:
                    assert(event["event"]=="updateParticipantsCount")
                    participantCount = event["participantsCount"]
                    participantsPerGame = event["participantsPerGame"]
                    titleLabel.text = f'Waiting for participants to join ({participantCount}/{participantsPerGame})'
                    for i in range(min(5,event["participantsCount"])):
                        show(self.ids[f'pfp{i}'])
                event = await self.qApp.get()

            assert(event["event"]=="gameStart")
            print("gameStart event received by app")
            self.gameStarted = True
            gameInfo = event
            titleLabel.text = f'Game is starting ({participantCount}/{participantsPerGame})'
            bodyLabel.text = "The game will start shortly"
            # print(self.ids["exitButton"].background_color)
            self.ids["exitButton"].background_color = [0.5,0.5,0.5, 1]
            # print(self.ids["exitButton"].background_color)
            for i in range(min(5,len(gameInfo["participants"]))):
                p = gameInfo["participants"][i]
                self.ids[f'participantNickname{i}'].text = p["nickname"]

            if gameInfo["roundStartTime"]-now() > 0:
                print("Waiting for round start")
                await asyncio.sleep((gameInfo["roundStartTime"]-now())/1000)

            self.app.globalGameInfo = gameInfo
            self.manager.current = "game"

        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __joinRoom",str(e))
    
    def exitGame(self):
        if(self.gameStarted):
            print("Game started cannot exit")
        else:
            print("quit game")
            self.qGame.put_nowait({
                "event": "quitGame"
            })
            self.manager.current = "home"
            return
        