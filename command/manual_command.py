from kivy.uix.boxlayout import BoxLayout
import csv
import os
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime
import json
import requests
from kivy.clock import Clock

class ControllerManual(BoxLayout):
    # camera_status_controll = StringProperty("No") 
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.x_error=0
        self.y_error = 0
        self.postion_x = 0
        self.postion_y = 0
        self.static_speed_manual = 100
        # self.static_speed_manual_x = 400
        # self.static_speed_manual_y = 400
        self.step_input = 10
        self.helio_stats_selection = ""
        self.helio_stats_endpoint = ""
        self.camera_selection = ""
        self.camera_endpoint = ""
        self.url_request_update = ""
        self.static_manaul_dict = {
            "up": "up", 
            "down": "down",  
            "left":"reverse", 
            "left_down": "bottom_left", 
            "left_up":"top_left", 
            "right": "forward", 
            "right_down": "bottom_right",   
            "right_up": "top_right" 
            }
        self.static_get_api_helio_stats_endpoint = "http://192.168.0.106/"
        Clock.schedule_once(lambda dt: self.loop_checking_status())

    def show_popup_camera(self, message):
        popup = Popup(title='Camera status',
                content=Label(text=message),
                size_hint=(0.6, 0.4))
        popup.open()

    def push_upper(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['up'],
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }
                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    def push_left(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['left'],
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    def push_right(self):
        # print(self.static_manaul_dict['right'])
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['right'], 
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    print(payload_set)
                    print(self.helio_stats_endpoint)
                    print(response)
                    
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    def push_down(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['down'],
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    def haddle_stop(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                payload_set = {
                    "topic":"stop"
                }
                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    ### on imp ###
    def push_right_down(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['right_down'],
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    ### on imp ###
    def push_left_down(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['left_down'],
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    ### on imp ###
    def push_left_up(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['left_up'],
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    ### on imp ###
    def push_right_up(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_selection != "":
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
                payload_set = {
                    "topic":self.static_manaul_dict['right_up'],
                    "step": setting_data['control_speed_distance']['distance_mm'],
                    "speed": setting_data['control_speed_distance']['speed_screw'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+self.helio_stats_endpoint +"/update-data", json=payload_set)
                    if response.status_code == 200:
                        pass
                    else:
                        self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
                except Exception as e:
                    self.show_popup("Error", f"Connecton error {str(e)}")
            else:
                self.show_popup("Alert", "Please helio stats and camera")
        else:
            self.show_popup("Alert", "Please start camera")

    

    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(600, 300))
        popup.open()
    
    ### this loop will check status every 1 sec ###
    def update_status_now(self, dt):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            # self.__extract_coordinates(self.error_center_f.text, self.error_center_t.text)

            if self.helio_stats_id_manual.text != "None" and self.camera_url_id_manual.text  != "None":
                if ("ID: "+self.helio_stats_selection) != self.helio_stats_id_manual.text and ("ID: "+self.camera_selection) != self.camera_url_id_manual.text:
                    self.helio_stats_selection =  self.__extract_coordinates_selection(self.helio_stats_id_manual.text)
                    self.camera_selection =  self.__extract_coordinates_selection(self.camera_url_id_manual.text)
                    self.__find_address_by_id()
                    # print("Chnage init")
                    # self.show_popup("Alert", "Parameter have change")
                    # print(self.helio_stats_endpoint)
                    # print(self.camera_endpoint)

    def loop_checking_status(self):
        Clock.schedule_interval(self.update_status_now, 1)

    def update_and_submit(self):
        if int(self.number_center_light.text) == 1:
            self.__haddle_submit_cap_error()
        else:
            self.show_popup("Alert", f"Light center must detected equal 1.")

    def __haddle_submit_cap_error(self):
        status_camera = self.__checking_status_camera_open()
        print(status_camera)
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_endpoint != "":
                try:
                    payload = requests.get(url="http://"+self.static_get_api_helio_stats_endpoint)
                    setJson = payload.json()

                    now = datetime.now()
                    timestamp = now.strftime("%d/%m/%y %H:%M:%S")

                    adding_time = {
                        "timestamp": timestamp,
                        "helio_stats_id": self.helio_stats_selection,
                        "camera_use": self.camera_endpoint,
                        "id":  setJson['id'],
                        "currentX":  setJson['currentX'],
                        "currentY": setJson['currentY'],
                        "err_posx": setJson['err_posx'],
                        "err_posy": setJson['err_posy'],
                        "x": setJson['safety']['x'],
                        "y": setJson['safety']['y'],
                        "x1": setJson['safety']['x1'],
                        "y1": setJson['safety']['y1'], 
                        "ls1": setJson['safety']['ls1'],
                        "st_path": setJson['safety']['st_path'],
                        "move_comp": setJson['safety']['move_comp'],
                        "elevation": setJson['elevation'],
                        "azimuth": setJson['azimuth'],
                        "control_by": "human"
                    }

                    filename = "./data/result/error_data.csv"
                    filepath = os.path.join(os.getcwd(), filename)
                    try:
                        fieldnames = adding_time.keys()
                        with open(filepath, mode='a', newline='', encoding='utf-8') as csv_file:
                            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                            writer.writerow(adding_time)
                        self.show_popup("Error alert",f"Data successfully saved to {filename}.")
                    except Exception as e:
                        self.show_popup("Error alert",f"Error saving file:\n{str(e)}")
                except Exception as e:
                    self.show_popup("Error alert",f"{e}")
            else:
                self.show_popup("Alert",f"Please helio stats and camera")
        else:
            self.show_popup("Alert",f"Please start camera")
        

    def __extract_coordinates_selection(self, selection):
        return selection.split(": ")[1]
    
    def __checking_status_camera_open(self):
        if self.camera_is_open.text == "Manual menu || Camera status:On":
            return True
        
    def __find_address_by_id(self):
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
            
            h_id = self.__extract_coordinates_selection(self.helio_stats_id_manual.text)
            c_id = self.__extract_coordinates_selection(self.camera_url_id_manual.text)

            for helio_data in storage['helio_stats_ip']:
                if h_id == helio_data['id']:
                    self.helio_stats_endpoint = helio_data['ip']
                    break

            for camera_data in storage['camera_url']:
                if c_id == camera_data['id']:
                    self.camera_endpoint = camera_data['url']
                    break
        except Exception as e:
            self.show_popup("Error", f"{e}")
    
    # def __extract_coordinates(self, s_1, s_2):
    #     pattern = r'X:\s*(\d+)px\s*Y:\s*(\d+)px'

    #     match = re.search(pattern, s_1)
    #     match_2 = re.search(pattern, s_2)

    #     if match:
    #         if match_2:
    #             self.x_error = int(match.group(1)) - int(match_2.group(1))
    #             self.y_error = int(match.group(2)) - int(match_2.group(2))
    #             self.postion_x = int(match_2.group(1))
    #             self.postion_y = int(match_2.group(2))
    #         else:
    #             print("The string format is incorrect.")
    #     else:
    #         print("The string format is incorrect.")



