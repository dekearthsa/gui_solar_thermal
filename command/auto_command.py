from kivy.uix.boxlayout import BoxLayout
import paho.mqtt.client as mqtt
import csv
import os
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime
import re
from kivy.clock import Clock
import json

class ControllerAuto(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mqtt_host = "mqtt-dashboard.com"
        self.mqtt_port = "8884"
        self.mqtt_client = mqtt.Client() 
        self.mqtt_topic = "testtopic/1"
        self.turn_on_auto_mode = False
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        Clock.schedule_once(lambda dt: self.mqtt_connection())
        Clock.schedule_once(lambda dt: self.fetch_helio_stats_list())
        self.speed_screw = 1
        self.distance_mm = 1 
        self.is_auto_on = False
        self.static_title_mode = "Auto menu || Camera status:On"
        self.array_helio_stats = []
        self.time_loop_update = 2 ## 2 sec test update frame
    def fetch_helio_stats_list(self):
        with open('./data/setting/connection.json', 'r') as file:
            data = json.load(file)

        self.array_helio_stats = data['helio_stats_ip']
        self.ids.helio_stats_operate.text = "Helio stats: " + data['helio_stats_ip'][0]['id']

    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(400, 200))
        popup.open()

    def mqtt_connection(self):
        self.ids.mqtt_connection_status_auto.text = "Mqtt connecting..."
        try:
            # Connect to the MQTT broker
            self.mqtt_client.connect(self.mqtt_host)
            # Start the network loop in a separate thread
            self.mqtt_client.loop_start()
            print("MQTT connection established and loop started.")
        except Exception as e:
            self.ids.mqtt_connection_status_auto.text = "Fail to connect mqtt broker"
            print(f"MQTT connection failed: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.ids.mqtt_connection_status_auto.text = "Mqtt connected"
            print("MQTT Connection Successful")
        else:
            self.ids.mqtt_connection_status_auto.text = "Mqtt connecting"
            print(f"MQTT Connection Failed with code {rc}")

    def on_disconnect(self,client, userdata, rc):
        print("MQTT Disconnected")

    def active_auto_mode(self):
        if self.status_auto.text == self.static_title_mode:
            if self.turn_on_auto_mode == False:
                self.turn_on_auto_mode = True
                self.ids.label_auto_mode.text = "Auto on"
                self.__on_loop_auto_calculate_diff()
            else:
                self.turn_on_auto_mode = False
                self.ids.label_auto_mode.text = "Auto off"
                self.__off_loop_auto_calculate_diff()
        else: 
            self.show_popup("Camera status", f"Please turn on camera.")

    def update_loop_calulate_diff(self, dt):
        diff_x, diff_y = self.__extract_coordinates(self.center_frame_auto.text, self.center_target_auto.text)
        self.__send_payload(diff_x=diff_x, diff_y=diff_y)

    def __on_loop_auto_calculate_diff(self):
        Clock.schedule_interval(self.update_loop_calulate_diff, self.time_loop_update)

    def __off_loop_auto_calculate_diff(self):
        Clock.unschedule(self.update_loop_calulate_diff)

    def __extract_coordinates(self, s1, s2):
        pattern = r'X:\s*(\d+)px\s*Y:\s*(\d+)px'
        match = re.search(pattern, s1)
        match_2 = re.search(pattern, s2)
        if match:   
            if match_2:
                diff_x = int(match.group(1)) - int(match_2.group(1))
                diff_y = int(match.group(2)) - int(match_2.group(2))
                return diff_x, diff_y
        else:
            print("The string format is incorrect.")

    def __send_payload(self, diff_x, diff_y):
        debug_topic = "helio_stats_h1"
        payload = {
                "opt": "auto",
                "direction":{
                    "x":{
                        "distance": diff_x,
                        "speed": self.speed_screw
                    },
                    "y":{
                        "distance":diff_y,
                        "speed": self.speed_screw
                    }
                },
            }
        
        self.mqtt_client.publish(debug_topic,str(payload))
        self.__haddle_save_positon(diff_x=diff_x, diff_y=diff_y)
    # def __update_label_helio_stats(self, helio_stats_id):
    #     self.ids.helio_stats_operate.text = "Helio stats: " + helio_stats_id      

    def __haddle_save_positon(self, diff_x, diff_y):
        now = datetime.now()
        timestamp = now.strftime("%d/%m/%y %H:%M:%S")

        adding_time = {
            "timestamp": timestamp,
            "x_error":  diff_x,
            "y_error": diff_y,
            "speed": self.speed_screw
        }

        filename = "./data/result/error_data.csv"
        filepath = os.path.join(os.getcwd(), filename)
        try:
            fieldnames = adding_time.keys()
            with open(filepath, mode='a', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writerow(adding_time)
        except Exception as e:
            self.turn_on_auto_mode = False
            self.ids.label_auto_mode.text = "Auto off"
            self.__off_loop_auto_calculate_diff()
            self.show_popup(f"Error saving file:\n{str(e)}")