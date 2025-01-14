from kivy.uix.popup import Popup
from kivy.uix.actionbar import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
class PopupShowSaveValueCropFrame(Popup):
   def __init__(self, **kwargs):
      super().__init__(**kwargs)
      self.title = "Alert"
      self.size_hint = (0.6, 0.4)
