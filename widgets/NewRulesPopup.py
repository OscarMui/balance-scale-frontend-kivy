import asyncio

from kivy.properties import (NumericProperty)
from kivy.uix.popup import Popup
from common.visibility import show, hide

class NewRulesPopup(Popup):

    def __init__(self,origPNum,newPNum, titleText="Someone died!", hintText="You can always review these rules by clicking the (?) button on the top-right corner.", allowClose=False, **kwargs):
        super(NewRulesPopup, self).__init__(**kwargs)
        assert(origPNum in [2,3,4],"origPNum in [2,3,4]")
        assert(newPNum in [2,3,4],"newPNum in [2,3,4]")

        self.title = titleText
        self.ids["hintText"].text = hintText
        # show already existing rules
        for i in range(origPNum,5):
            show(self.ids[f"rule{i}"])
        self.handlePopupTask = asyncio.create_task(self.__handlePopup(origPNum,newPNum,allowClose))
        
    async def __handlePopup(self,origPNum,newPNum,allowClose):
        try:
            # show the rest of the rules after 1 sec
            await asyncio.sleep(1)

            for i in range(newPNum,origPNum):
                self.ids[f"rule{i}"].color = (0,1,1,1)
                show(self.ids[f"rule{i}"],animation=True)
                
            if allowClose:
                await asyncio.sleep(4)
                show(self.ids["closeButton"])

        except Exception as e:
            # We need to print the exception or else it will fail silently
            print("ERROR __handlePopup",repr(e))

        

