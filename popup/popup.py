# from kivy.app import App
from kivy.uix.popup import Popup
# from kivy.uix.label import Label
# from kivy.properties import ObjectProperty

## This class using for show widget PopupShowSaveValueCropFrame ## 
class PopupShowSaveValueCropFrame(Popup):
     def __init__(self, **kwargs):
        super(PopupShowSaveValueCropFrame, self).__init__(**kwargs)
        self.title = "Alert"
        self.size_hint = (0.6, 0.4)


class PopupShowAlertButtonChangeStatus(Popup):
    def __init__(self, **kwargs):
        super(PopupShowAlertButtonChangeStatus, self).__init__(**kwargs)
        self.title = "Alert"
        self.size_hint = (0.6, 0.4)



