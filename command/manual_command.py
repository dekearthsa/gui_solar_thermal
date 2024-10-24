from kivy.uix.boxlayout import BoxLayout
import csv
import os
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime
import re

class ControllerManual(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x_error = 0
        self.y_error = 0

    def push_upper(self):
        pass
    def push_left(self):
        pass    
    def push_right(self):
        pass
    def push_down(self):
        pass

    def __haddle_submit_cap_error(self):
        now = datetime.now()
        timestamp = now.strftime("%d/%m/%y %H:%M:%S")

        adding_time = {
            "timestamp": timestamp,
            "x_error":  self.x_error,
            "y_error":  self.y_error
        }

        filename = "./data/result/error_data.csv"
        filepath = os.path.join(os.getcwd(), filename)
        try:

            fieldnames = adding_time.keys()

            with open(filepath, mode='a', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writerow(adding_time)

            self.show_popup(f"Data successfully saved to {filename}.")

        except Exception as e:
            self.show_popup(f"Error saving file:\n{str(e)}")

    def show_popup(self, message):
        popup = Popup(title='Save Status',
                content=Label(text=message),
                size_hint=(0.6, 0.4))
        popup.open()

    def update_and_submit(self):
        self.__extract_coordinates(self.error_center_f.text)
        self.__haddle_submit_cap_error()

    def __extract_coordinates(self, s):
        numbers = re.findall(r'-?\d+', s)
        if len(numbers) >= 2:
            x, y = map(int, numbers[:2])
            self.x_error = x
            self.y_error = y
            # return x, y
        else:
            self.show_popup(f"Error extract format:\n{s}")