import asyncio

from kivy.properties import (NumericProperty)
from kivy.uix.popup import Popup
from common.visibility import show, hide

class NewRulesPopup(Popup):

    def __init__(self,origPNum,newPNum, titleText="Someone died!", **kwargs):
        super(NewRulesPopup, self).__init__(**kwargs)

        self.title = titleText
        # show already existing rules
        for i in range(origPNum,5):
            show(self.ids[f"rule{i}"])
        self.handlePopupTask = asyncio.create_task(self.__handlePopup(origPNum,newPNum))
    
    async def __handlePopup(self,origPNum,newPNum):
        try:
            # show the rest of the rules after 1 sec
            await asyncio.sleep(1)

            for i in range(newPNum,origPNum):
                self.ids[f"rule{i}"].color = (0,1,1,1)
                show(self.ids[f"rule{i}"],animation=True)
        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __handlePopup",repr(e))

        

