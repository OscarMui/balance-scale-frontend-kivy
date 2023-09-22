from kivy.uix.button import Button

class ImageButton(Button):
    
    def __init__(self, **kwargs):
        super(ImageButton, self).__init__(**kwargs)
        
        # initially set width to height
        self.width = self.height

        # set again whenever size changes
        self.bind(height=self.set_button_width)

    def set_button_width(self, instance, height):
        self.width = height  # Set button width equal to its height