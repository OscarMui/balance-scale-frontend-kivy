from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import datetime

from common.now import now
from common.visibility import hide, show
from widgets.WrapLabel import WrapLabel

class Announcement(BoxLayout):
    def __init__(self, a, **kwargs):
        super(Announcement, self).__init__(**kwargs)
        
        self.a = a
        if a["type"] == "client":
            if a["shortCode"] == "discord-gaming-session":
                self.ids["btn"].background_normal = "assets/discord-gaming-session.png"
                self.ids["btn"].background_down = "assets/discord-gaming-session.png"

        self.updateTimer()

    def showDetails(self):
        try:
            a = self.a
            if a["type"] == "server":
                popup = Popup(
                    title=a["title"], 
                    content=WrapLabel(text=a["body"]),
                    size_hint=(0.8, 0.4),
                )
                popup.open()
            else:
                assert(a["type"]=="client",'a["type"]=="client"')
                if a["shortCode"] == "discord-gaming-session":
                    localTime = datetime.datetime.fromtimestamp(a["eventTime"]//1000)
                    # Format the datetime as a string
                    timeString = localTime.strftime('%Y-%m-%d %H:%M')
                    popup = Popup(
                        title="Discord Gaming Session", 
                        content=WrapLabel(text=f"We host gaming sessions on our Discord channel from time to time. The next session would be on {timeString} (your local time). Join our Discord for more info!"),
                        size_hint=(0.8, 0.4),
                    )
                    popup.open()

                
        except Exception as e:
            # non-essential work, catch it and contine with other things
            print("Error in Announcement.py show details",repr(e))
    
    def updateTimer(self):
        try:
            a = self.a
            timer = self.ids["timer"]

            if "eventTime" in a and a["eventTime"] > now():
                minutes = (a["eventTime"]-now())//1000//60

                # modify timer
                timer.text = f'\n{minutes // 1440}d {minutes % 1440 // 60}h {minutes % 60}m' # the newline is necessary for proper alignment
                    
                show(timer)
            elif "shortCode" in a and a["shortCode"] == "discord-gaming-session":
                timer.text = '\nRIGHT NOW!'
                show(timer)
            else:
                hide(timer)
        except Exception as e:
            # non-essential work, catch it and contine with other things
            print("Error in Announcement.py update timer",repr(e))
    