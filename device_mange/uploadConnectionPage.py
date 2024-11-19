import os
import json
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup

# Ensure that FileChooserPopup is accessible
from .fileChooserPopup import FileChooserPopup  # Assuming FileChooserPopup is in the same 'widget' package
from kivy.app import App

class UploadConnectionPage(Screen):
    
    SAVE_DIR = os.path.join(os.getcwd(), 'data', 'setting')
    SAVE_FILE = 'connection.json'
    SAVE_PATH = os.path.join(SAVE_DIR, SAVE_FILE)

    def open_file_dialog(self):
        content = FileChooserPopup(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Select JSON File",
                            content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    # def receive_text(self, text):
    #     app = App.get_running_app()
    #     current_mode = app.current_mode  # Assuming you have a global property 'current_mode'
    #     if current_mode != "connection_upload":
    #         print(current_mode)

    def __check__list_connection(self, data):
        print(data)
        if data['helio_stats_ip']:
            if data['camera_url']:
                return True
            else:
                return False
        else:
            return False


    def load(self, path, selection):
        if selection:
            selected_path = selection[0]
            try:
                with open(selected_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                is_format = self.__check__list_connection(data)
                if is_format == True:
                    self.display_json(data)
                    self.save_json(data)
                    self.dismiss_popup()
                    self.show_popup("Success", f'JSON saved to {self.SAVE_PATH}')
                else:
                    self.show_popup("Invalid json format", f'Invalid json format!')
            
            except json.JSONDecodeError as jde:
                self.show_popup("JSON Error", f"Invalid JSON file:\n{str(jde)}")
            except Exception as e:
                self.show_popup("Invalid json format", f'Invalid json format! \n{str(data)}')

        else:
            self.show_popup("Selection Error", "No file selected.")

    def dismiss_popup(self):
        if self._popup:
            self._popup.dismiss()

    def display_json(self, data, parent=None, indent=0):
        if parent is None:
            parent = self.ids.json_display
            parent.clear_widgets()

        if isinstance(data, dict):
            for key, value in data.items():
                label = Label(
                    text=f"{'  ' * indent}{key}: {self.format_value(value)}",
                    size_hint_y=None,
                    height=self.calculate_label_height(value),
                    halign='left',
                    valign='middle'
                )
                label.bind(size=label.setter('text_size'))
                parent.add_widget(label)
                if isinstance(value, (dict, list)):
                    self.display_json(value, parent, indent + 1)
        elif isinstance(data, list):
            for index, item in enumerate(data):
                label = Label(
                    text=f"{'  ' * indent}[{index}]: {self.format_value(item)}",
                    size_hint_y=None,
                    height=self.calculate_label_height(item),
                    halign='left',
                    valign='middle'
                )
                label.bind(size=label.setter('text_size'))
                parent.add_widget(label)
                if isinstance(item, (dict, list)):
                    self.display_json(item, parent, indent + 1)

    def format_value(self, value):
        if isinstance(value, (dict, list)):
            return ''
        return str(value)

    def calculate_label_height(self, value):
        if isinstance(value, (dict, list)):
            return '20dp'
        else:
            return '30dp'

    def save_json(self, data):
        try:
            # Ensure the save directory exists
            os.makedirs(self.SAVE_DIR, exist_ok=True)
            with open(self.SAVE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.show_popup("Save Error", f"Failed to save JSON:\n{str(e)}")

    def show_popup(self, title, message):
        popup_content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_label = Label(text=message)
        popup_button = Button(text="OK", size_hint=(1, 0.3))
        popup_content.add_widget(popup_label)
        popup_content.add_widget(popup_button)

        popup = Popup(title=title,
                        content=popup_content,
                        size_hint=(0.6, 0.4))
        popup_button.bind(on_release=popup.dismiss)
        popup.open()