from kivy.uix.boxlayout import BoxLayout
import paho.mqtt.client as mqtt
import csv
import os
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime
import re
from kivy.clock import Clock
from kivy.properties import StringProperty

class ControllerManual(BoxLayout):
    camera_status_controll = StringProperty("No") 
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_host = "mqtt-dashboard.com"
        self.mqtt_port = "8884"
        self.mqtt_client = mqtt.Client() 
        self.mqtt_topic = "testtopic/1"
        self.x_error = 0
        self.y_error = 0
        self.dynamic_move_upper = 0
        self.dynamic_move_left = 0
        self.dynamic_move_right = 0
        self.dynamic_move_down = 0
        self.postion_x = 0
        self.postion_y = 0
        self.first_pos_x = 0
        self.first_pos_y = 0
        self.is_first_pos = False
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        Clock.schedule_once(lambda dt: self.mqtt_connection())
        self.speed_screw = 1
        self.distance_mm = 1 

        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.ids.mqtt_connection_status_manual.text = "Mqtt connected"
            print("MQTT Connection Successful")
        else:
            self.ids.mqtt_connection_status_manual.text = "Mqtt connecting..."
            print(f"MQTT Connection Failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("MQTT Disconnected")

    def mqtt_connection(self):
        self.ids.mqtt_connection_status_manual.text = "Mqtt connecting..."
        try:
            # Connect to the MQTT broker
            self.mqtt_client.connect(self.mqtt_host)
            # Start the network loop in a separate thread
            self.mqtt_client.loop_start()
            print("MQTT connection established and loop started.")
        except Exception as e:
            self.ids.mqtt_connection_status_manual.text = "Fail to connect mqtt broker"
            print(f"MQTT connection failed: {e}")

    def show_popup_camera(self, message):
        popup = Popup(title='Camera status',
                content=Label(text=message),
                size_hint=(0.6, 0.4))
        popup.open()

    def push_upper(self):
        # self.haddle_save_first_pos()
        # print(self.camera_status_controll)
        if self.camera_status_controll == "On":
            payload = {
                "opt": "manual",
                "direction":{
                    "x":{
                        "distance": 0,
                        "speed": self.speed_screw
                    },
                    "y":{
                        "distance": self.distance_mm,
                        "speed": self.speed_screw
                    }
                },
            }
            self.mqtt_client.publish(self.mqtt_topic, str(payload))
        else:
            self.show_popup_camera("Camera is off")

    def push_left(self):
        # self.haddle_save_first_pos()
        if self.camera_status_controll == "On":
            payload = {
                "opt": "manual",
                "direction":{
                    "x":{
                        "distance": self.distance_mm,
                        "speed": self.speed_screw
                    },
                    "y":{
                        "distance": 0,
                        "speed": self.speed_screw
                    }
                },
            }
            self.mqtt_client.publish(self.mqtt_topic, str(payload))   
        else:
            self.show_popup_camera("Camera is off")
    def push_right(self):
        # self.haddle_save_first_pos()
        if self.camera_status_controll == "On":
            payload = {
                "opt": "manual",
                "direction":{
                    "x":{
                        "distance": self.distance_mm,
                        "speed": self.speed_screw
                    },
                    "y":{
                        "distance": 0,
                        "speed": self.speed_screw
                    }
                },
            }
            self.mqtt_client.publish(self.mqtt_topic, str(payload))
        else:
            self.show_popup_camera("Camera is off")

    def push_down(self):
        # self.haddle_save_first_pos()
        if self.camera_status_controll == "On":
            payload = {
                "opt": "manual",
                "direction":{
                    "x":{
                        "distance":0,
                        "speed": self.speed_screw
                    },
                    "y":{
                        "distance": self.distance_mm,
                        "speed": self.speed_screw
                    }
                },
            }
            self.mqtt_client.publish(self.mqtt_topic, str(payload))
        else:
            self.show_popup_camera("Camera is off")

    def __haddle_submit_cap_error(self):
        now = datetime.now()
        timestamp = now.strftime("%d/%m/%y %H:%M:%S")

        adding_time = {
            "timestamp": timestamp,
            "x_error":  self.x_error,
            "y_error":  self.y_error,
            "speed": self.speed_screw
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
        self.__extract_coordinates(self.error_center_f.text, self.error_center_t.text)
        self.__haddle_submit_cap_error()

    def __extract_coordinates(self, s_1, s_2):
        pattern = r'X:\s*(\d+)px\s*Y:\s*(\d+)px'

        match = re.search(pattern, s_1)
        match_2 = re.search(pattern, s_2)

        if match:
            if match_2:
                self.x_error = int(match.group(1)) - int(match_2.group(1))
                self.y_error = int(match.group(2)) - int(match_2.group(2))
                self.postion_x = int(match_2.group(1))
                self.postion_y = int(match_2.group(2))
            else:
                print("The string format is incorrect.")
        else:
            print("The string format is incorrect.")