from kivy.uix.popup import Popup

class PopupShowSaveValueCropFrame(Popup):
     def __init__(self, **kwargs):
        super(PopupShowSaveValueCropFrame, self).__init__(**kwargs)
        self.title = "Alert"
        self.size_hint = (0.6, 0.4)



