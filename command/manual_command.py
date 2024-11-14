from kivy.uix.boxlayout import BoxLayout
import csv
import os
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime
import json
import requests
from kivy.clock import Clock
import re

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
        # Clock.schedule_once(lambda dt: self.loop_checking_status())

    def show_popup_camera(self, message):
        popup = Popup(title='Camera status',
                content=Label(text=message),
                size_hint=(0.6, 0.4))
        popup.open()

    def push_upper(self):
        status_camera = self.__checking_status_camera_open()
        if status_camera == True:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['up'],
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }
                print(payload_set)
                print("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data")
                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['left'],
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }
                print(payload_set)
                print(setting_data['storage_endpoint']['helio_stats_ip']['ip'])
                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['right'], 
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['down'],
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":"stop"
                }
                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['right_down'],
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['left_down'],
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['left_up'],
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            if setting_data['storage_endpoint']['helio_stats_ip']['ip'] != "" and setting_data['storage_endpoint']['camera_ip']['ip'] != "":
                payload_set = {
                    "topic":self.static_manaul_dict['right_up'],
                    "step": setting_data['control_speed_distance']['manual_mode']['step'],
                    "speed": setting_data['control_speed_distance']['manual_mode']['speed'],
                    # "speed_y": self.static_speed_manual_y,
                }

                try:
                    response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/update-data", json=payload_set, timeout=5)
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
    

    def update_and_submit(self):
        if int(self.number_center_light.text) == 1:
            self.__haddle_submit_cap_error()
        else:
            self.show_popup("Alert", f"Light center must detected equal 1.")

    def __haddle_submit_cap_error(self):
        status_camera = self.__checking_status_camera_open()
        # print(status_camera)
        if status_camera == True:
            if self.helio_stats_selection != "" and self.camera_endpoint != "":
                try:
                    with open('./data/setting/setting.json', 'r') as file:
                        setting_data = json.load(file)
                    payload = requests.get(url="http://"+self.static_get_api_helio_stats_endpoint)
                    setJson = payload.json()

                    now = datetime.now()
                    timestamp = now.strftime("%d/%m/%y %H:%M:%S")

                    adding_time = {
                        "timestamp": timestamp,
                        "helio_stats_id": setting_data['storage_endpoint']['helio_stats_ip']['id'],
                        "camera_use": setting_data['storage_endpoint']['camera_ip']['id'],
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
        

    # def __extract_coordinates_selection(self, selection):
    #     return selection.split(": ")[1]
    
    def __checking_status_camera_open(self):
        if self.camera_is_open.text == "Manual menu || Camera status:On":
            return True
    
    #### for test ####
    def __extract_coordinates_pixel(self, s1, s2): ##(frame_center, target_center)
        pattern = r'X:\s*(\d+)px\s*Y:\s*(\d+)px'
        match = re.search(pattern, s1)
        match_2 = re.search(pattern, s2)

        if match:   
            if match_2:
                center_x = int(match.group(1))
                center_x_light = int(match_2.group(1))
                
                center_y = int(match.group(2))
                center_y_light = int(match_2.group(2))

                return center_x, center_y, center_x_light, center_y_light
        else:
            print("The string format is incorrect.")

    def test_manual_send_payload_auto_2(self):
        
        center_x, center_y, target_x, target_y = self.__extract_coordinates_pixel(
            self.error_center_f.text, 
            self.error_center_t.text
            )
        
        print(center_x, center_y, target_y, target_y)
        
        _, _, frame_w, frame_h = self.haddle_extact_boarding_frame()

        scaling_x, scaling_y, scaling_height = self.haddle_convert_to_old_resolution(
            current_width=frame_w,
            current_height=frame_h
        )

        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            print(e)
            self.show_popup("Error get setting", f"Failed to get value in setting file: {e}")



        payload = {
                "topic":"auto",
                "axis": "x",
                "cx":int(target_x/scaling_x), # center x light
                "cy":int((scaling_height-target_y)/scaling_y), # center y light
                "target_x":int(target_x/scaling_x),
                "target_y":int((scaling_height-target_y)/scaling_y), # center y light
                "kp":1,
                "ki":1,
                "kd":2,
                "max_speed":setting_data['control_speed_distance']['manual_mode']['speed'],
                "off_set":1,
                "status": "1"
            }

        headers = {
            'Content-Type': 'application/json'  
        }

        print("payload in manual function => ",payload)

        try:
            response = requests.post("http://"+setting_data['storage_endpoint']['helio_stats_ip']['ip']+"/auto-data", data=json.dumps(payload), headers=headers, timeout=5)
            if response.status_code != 200:
                try:
                    error_info = response.json()
                    self.show_popup("Connection Error", f"{str(error_info)} \n auto mode off")
                except ValueError:
                    self.show_popup("Connection Error", f"{str(response.text)} \n auto mode off")
            else:
                print("debug send success! ",response)

        except Exception as e:
            self.show_popup("Connection Error", f"{str(e)} \n auto mode off")
            #self.turn_on_auto_mode = False
            #self.ids.label_auto_mode.text = "Auto off"
            #self.__off_loop_auto_calculate_diff() 

    def haddle_convert_to_old_resolution(self,current_width, current_height):
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            print(e)
            self.show_popup("Error get setting", f"Failed to get value in setting file: {e}")
    
        scaling_x = round((current_width/setting_data['old_frame_resolution']['width']),2) 
        scaling_y = round((current_height/setting_data['old_frame_resolution']['height']),2)

        return scaling_x, scaling_y, current_height
    

    def haddle_extact_boarding_frame(self):
        data = self.test_manual_send_payload_auto.text
        numbers = re.findall(r'\d+', data)
        int_numbers = [int(num) for num in numbers]
        return int_numbers[0], int_numbers[1], int_numbers[2], int_numbers[3]