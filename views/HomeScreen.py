import random
import webbrowser
import asyncio
import httpx
import re # regex

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from common.constants import APP_STORE_URL, CLIENT_VERSION, DISCORD_URL, GOOGLE_PLAY_URL, SERVER_URL
from widgets.RulesPopup import RulesPopup
from widgets.WrapLabel import WrapLabel

class HomeScreen(Screen):
    def __init__(self, qGame, qApp, store, name):
        super().__init__(name=name)
        self.qGame = qGame  
        self.qApp = qApp
        self.store = store
        self.app = App.get_running_app()
        self.allowOnline = False

        if self.store.exists('nicknameV1'):
            NICKNAME = self.store.get('nicknameV1')["value"]
            print('nicknameV1 exists:', NICKNAME)
            self.ids["nickname"].text = NICKNAME


    def on_pre_enter(self):
        # only run if it is the first time
        if self.app.globalNews == None:
            self.handleVersionTask = asyncio.create_task(self.__handleVersion())

        if self.store.exists('pidV1') and not self.store.get('pidV1')["value"] == None:
            self.handleGamesStatusTask = asyncio.create_task(self.__handleGamesStatus(self.store.get('pidV1')["value"]))
    
    async def __handleVersion(self):
        print("HTTP server:", SERVER_URL)
        print("Client version:", CLIENT_VERSION)
        onlineButton = self.ids["onlineButton"]
        onlineButton.disabled = True
        onlineButton.text = "Connecting..."
        try:
            async with httpx.AsyncClient() as client:
                timeout = httpx.Timeout(5.0, read=15.0)
                resp = await client.get(SERVER_URL + "/api/version", timeout=timeout)
                response = resp.json()
                assert(response["result"]=="success")
                if CLIENT_VERSION not in response["acceptedClientVersions"]:
                    popup = Popup(
                        title='Please update your app', 
                        content=WrapLabel(text='You need to update the app in order to play online.',pos_hint={'center_y': .5}),
                        size_hint=(0.8, 0.3),
                    )
                    popup.open()
                    self.app.globalNews = {"announcements":[],"tips":[]} # prevent this from running again
                    onlineButton.text = "Play Online"
                    onlineButton.background_color = (0,0.7,0,1)
                    # we will keep the button disabled in this case
                    return 
                else:
                    print("Version compatible")
                if CLIENT_VERSION not in response["preferredClientVersions"]:
                    popup = Popup(
                        title='New update available', 
                        content=WrapLabel(text='Update the app to access new features.',pos_hint={'center_y': .5}),
                        size_hint=(0.8, 0.3),
                    )
                    popup.open()
                    # but proceed with the stuff later, as it can still play online
                else:
                    print("Version preferred")
                self.app.globalNews = response["news"]
                onlineButton = self.ids["onlineButton"]
                onlineButton.text = "Play Online"
                onlineButton.background_color = (0,0.7,0,1)
                onlineButton.disabled = False
                self.allowOnline = True

        except asyncio.CancelledError as e:
            print('Version task is cancelled', e)
        except Exception as e:
            popup = Popup(
                title = "Online mode unavailable at the moment",
                content = WrapLabel(text=repr(e),pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3),
            )
            popup.open()
            onlineButton = self.ids["onlineButton"]
            onlineButton.text = "Reconnect"
            onlineButton.background_color = (0,0,0.7,1)
            onlineButton.disabled = False
            
            self.app.globalNews = {"announcements":[],"tips":[]} # prevent this from running again
            return 
        finally:
            # when canceled, print that it finished
            print('Done version task')

    async def __handleGamesStatus(self,pid):
        try:
            async with httpx.AsyncClient() as client:
                timeout = httpx.Timeout(5.0, read=15.0)
                resp = await client.post(SERVER_URL + "/api/gamesStatus", 
                    timeout=timeout, 
                    data={
                        "pid": pid,
                    },
                )
                response = resp.json()
                if(response["result"]=="error"):
                    raise Exception(response["errorMsg"])
                assert(response["result"]=="success")
                if(response["canReconnect"]):
                    self.qGame.put_nowait({
                        "event": "reconnectGame",
                        "pid": pid,
                    })
                    self.manager.current = "joinRoom"
                print('Games status task completed')
        except asyncio.CancelledError as e:
            print('Games status task is cancelled',e)
        except Exception as e:
            print('Games status task error',e)

    def modeSelection(self, mode):
        if(mode == "online" and self.app.globalNews == None):
            popup = Popup(
                title='Please wait', 
                content=WrapLabel(text='Connecting with server',pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3),
            )
            popup.open()
            return 
        
        if(mode == "online" and not self.allowOnline):
            self.handleVersionTask = asyncio.create_task(self.__handleVersion())
            return
        
        NICKNAME = self.ids["nickname"].text
        self.store.put('nicknameV1', value=NICKNAME)

        if(NICKNAME==""):
            popup = Popup(
                title='Nickname Error', 
                content=WrapLabel(text='Nickname cannot be blank',pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3),
            )
            popup.open()
            return 
        
        if(len(NICKNAME) > 12):
            popup = Popup(
                title='Nickname Error', 
                content=WrapLabel(text='Nickname cannot be longer than 12 characters.',pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3), 
            )
            popup.open()
            return 
        
        regex = re.compile(r'^[A-Za-z0-9_]+$')
        if(regex.match(NICKNAME) == None):
            popup = Popup(
                title='Nickname Error', 
                content=WrapLabel(text='Nickname can only contain English letters, digits and underscores.',pos_hint={'center_y': .5}),
                size_hint=(0.8, 0.3), 
            )
            popup.open()
            return 

        print(f'HomeScreen.playGame text: {NICKNAME}, mode {mode}')
        # put_nowait can be used because our queue does not have an upper limit
        
        self.app.globalNickname = NICKNAME

        self.qGame.put_nowait({
            "event": "modeSelection",
            "mode": mode,
            "nickname": NICKNAME,
        })

        self.manager.current = "joinRoom"
    
    def on_pre_leave(self):
        if hasattr(self,"popup"):
            self.popup.dismiss()
        if hasattr(self,"handleVersionTask"):
            self.handleVersionTask.cancel()
        if hasattr(self,"handleGamesStatusTask"):
            self.handleGamesStatusTask.cancel()
    
    def showRules(self):
        self.popup = RulesPopup(detail=True)
        self.popup.open()

    def openDiscord(self):
        webbrowser.open(DISCORD_URL)

    def openGooglePlay(self):
        webbrowser.open(GOOGLE_PLAY_URL)

    def openAppStore(self):
        webbrowser.open(APP_STORE_URL)