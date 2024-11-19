
import os
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.button import Button
from kivy.uix.popup import Popup  


class FileChooserPopup(BoxLayout):
    def __init__(self, load, cancel, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 10
        self.padding = 10

        # Initialize FileChooser
        self.filechooser = FileChooserIconView(filters=['*.json'], path=os.getcwd())
        self.add_widget(self.filechooser)

        # Buttons Layout
        button_layout = BoxLayout(size_hint=(1, 0.1), spacing=10)
        load_button = Button(text="Load")
        cancel_button = Button(text="Cancel")
        button_layout.add_widget(load_button)
        button_layout.add_widget(cancel_button)
        self.add_widget(button_layout)

        # Bind buttons
        load_button.bind(on_release=lambda x: load(self.filechooser.path, self.filechooser.selection))
        cancel_button.bind(on_release=lambda x: cancel())
