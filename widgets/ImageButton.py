from kivy.uix.button import Button

class ImageButton(Button):
    
    def __init__(self, **kwargs):
        super(ImageButton, self).__init__(**kwargs)

        # set again whenever height/width changes
        self.bind(height=self.set_button_width)
        # self.bind(width=self.set_button_height, height=self.set_button_width)

    def set_button_width(self, instance, height):
        # if((not hasattr(self,"primary_dimension")) or self.primary_dimension == "y"):
        # print("set_button_width")
        ratio = self.ratio if hasattr(self,"ratio") else 1
        self.width = height*ratio  # Set button width equal to its height*ratio

    # def set_button_height(self, instance, width):
    #     if(hasattr(self,"primary_dimension") and self.primary_dimension == "x"):
    #         print("set_button_height")
    #         ratio = self.ratio if hasattr(self,"ratio") else 1
    #         self.height = width/ratio  