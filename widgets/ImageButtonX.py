from kivy.uix.button import Button

class ImageButtonX(Button):
    
    def __init__(self, **kwargs):
        super(ImageButtonX, self).__init__(**kwargs)

        # set again whenever height/width changes
        self.bind(width=self.set_button_height)

    def set_button_height(self, instance, width):
        print("set_button_height")
        ratio = self.ratio if hasattr(self,"ratio") else 1
        self.height = width/ratio  