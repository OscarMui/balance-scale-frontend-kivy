from kivy.uix.label import Label

class WrapLabel(Label):
    pass
    def __init__(self, **kwargs):
        super(WrapLabel, self).__init__(**kwargs)

        # set again whenever size changes/ text changes
        self.bind(text=self.set_label_size)
        self.bind(size_hint=self.set_label_size)

    def set_label_size(self, instance, text):
        self.text_size = (self.width, None)
        self.height = self.texture_size[1]