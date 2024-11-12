from kivy.uix.boxlayout import BoxLayout
import csv
import os
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from datetime import datetime
import re
from kivy.clock import Clock
import json
import requests

class ControllerAuto(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.helio_stats_id_endpoint = "" ### admin select helio stats endpoint
        self.helio_stats_selection_id = "" ####  admin select helio stats id
        self.camera_endpoint = ""
        self.camera_selection = ""
        self.turn_on_auto_mode = False

        # Clock.schedule_once(lambda dt: self.fetch_helio_stats_list()) mtd56790
        self.speed_screw = 1
        self.distance_mm = 1 
        self.is_auto_on = False
        self.static_title_mode = "Auto menu || Camera status:On"
        self.array_helio_stats = []
        self.time_loop_update = 5 ## 2 sec test update frame
        self.stop_move_helio_x_stats = 12 ### Stop move axis x when diff in theshold
        self.stop_move_helio_y_stats = 12 ### Stop move axis y when diff in theshold
        self.static_get_api_helio_stats_endpoint = "http://192.168.0.106/"
        
        self.set_axis = "x"
        self.set_kp = 1
        self.set_ki = 1
        self.set_kd = 2
        self.set_max_speed = 100
        self.set_off_set = 1
        self.set_status ="1"

    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(400, 200))
        popup.open()

    ### camera endpoint debug ###
    def selection_url_by_id(self):
        try:
            with open('./data/setting/setting.json', 'r') as file:
                storage = json.load(file)

            self.helio_stats_id_endpoint = storage['storage_endpoint']['helio_stats_ip']['ip']
            self.camera_endpoint = storage['storage_endpoint']['camera_ip']['ip']
            h_id =  storage['storage_endpoint']['helio_stats_ip']['id']
            c_id = storage['storage_endpoint']['camera_ip']['id']
            # for helio_data in storage['helio_stats_ip']:
            #     if h_id == helio_data['id']:
            #         self.helio_stats_id_endpoint = helio_data['ip']
            #         break

            # for camera_data in storage['camera_url']:
            #     if c_id == camera_data['id']:
            #         self.camera_endpoint = camera_data['url']
            #         break
            return h_id, c_id
        except Exception as e:
            self.show_popup("Error", f"{e}")

    def active_auto_mode(self):
        h_id, _ = self.selection_url_by_id()
        if self.camera_endpoint != "" and self.helio_stats_id_endpoint != "":
            if self.status_auto.text == self.static_title_mode:
                if self.turn_on_auto_mode == False:
                    if int(self.number_center_light.text) == 1:
                        self.turn_on_auto_mode = True
                        self.helio_stats_selection_id = h_id
                        self.ids.label_auto_mode.text = "Auto on"
                        self.__on_loop_auto_calculate_diff()
                    else:
                        self.show_popup("Alert", f"Light center must detected equal 1.")
                else:
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
            else: 
                self.show_popup("Alert", f"Please turn on camera.")
        else:
            self.show_popup("Alert", f"Please select helio stats id and camera")

    def update_loop_calulate_diff(self, dt):
        center_x, center_y, target_x, target_y = self.__extract_coordinates_pixel(self.center_frame_auto.text, self.center_target_auto.text)
        if self.status_auto.text == self.static_title_mode:
                now = datetime.now()
                timestamp = now.strftime("%d/%m/%y %H:%M:%S")
                if abs(center_x - target_x) <= self.stop_move_helio_x_stats and abs(center_y - target_y) <= self.stop_move_helio_y_stats:
                    try:
                        # with open('./data/setting/setting.json', 'r') as file:
                        #     setting_data = json.load(file)
                        payload = requests.get(url=self.static_get_api_helio_stats_endpoint)
                        # print("payload => ", payload)
                        setJson = payload.json()
                        # print(setJson)
                        # setJson = json.dumps(payload)
                        self.__haddle_save_positon(
                            timestamp=timestamp,
                            helio_stats_id=self.helio_stats_selection_id,
                            camera_use = self.camera_endpoint,
                            id=setJson['id'],
                            currentX=setJson['currentX'],
                            currentY=setJson['currentY'],
                            err_posx=setJson['err_posx'],
                            err_posy=setJson['err_posy'],
                            x=setJson['safety']['x'],
                            y=setJson['safety']['y'],
                            x1=setJson['safety']['x1'],
                            y1=setJson['safety']['y1'],
                            ls1=setJson['safety']['ls1'],
                            st_path=setJson['safety']['st_path'],
                            move_comp=setJson['safety']['move_comp'],
                            elevation=setJson['elevation'],
                            azimuth=setJson['azimuth'],
                        )
                    except Exception as e:
                        self.show_popup("Connection Error", f"{str(e)} \n auto mode off")
                        self.turn_on_auto_mode = False
                        self.ids.label_auto_mode.text = "Auto off"
                        self.__off_loop_auto_calculate_diff()
                else:
                    self.__send_payload(
                        axis=self.set_axis,
                        center_x=center_x, # frame x 
                        center_y=center_y, # frame y
                        center_y_light=target_y, # center_y_light
                        center_x_light=target_x, # center_x_light
                        kp=self.set_kp,
                        ki=self.set_ki,
                        kd=self.set_kd,
                        max_speed=self.set_max_speed,
                        off_set=self.set_off_set,
                        status=self.set_status
                        )
        else:
            self.show_popup("Alert", "Camera is offline.")
            self.turn_on_auto_mode = False
            self.ids.label_auto_mode.text = "Auto off"
            self.__off_loop_auto_calculate_diff()

    def __on_loop_auto_calculate_diff(self):
        Clock.schedule_interval(self.update_loop_calulate_diff, self.time_loop_update)

    def __off_loop_auto_calculate_diff(self):
        Clock.unschedule(self.update_loop_calulate_diff)

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

    def __send_payload(self, axis, 
                    center_x, 
                    center_y,
                    center_x_light,
                    center_y_light,
                    kp,ki,kd,max_speed,off_set,status):
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            print(e)
            self.show_popup("Error get setting", f"Failed to get value in setting file: {e}")

        _, _, frame_w, frame_h = self.haddle_extact_boarding_frame()
        scaling_x, scaling_y, scaling_height = self.haddle_convert_to_old_resolution(
            current_width=frame_w,
            current_height=frame_h
        )

        payload = {
                "topic":"auto",
                "axis": axis,
                # "cx": int(center_x_light/scaling_x),
                # "cy": int(center_y_light/scaling_y),
                # "target_x": int(center_x/scaling_x),
                # "target_y": int(center_y/scaling_y),
                "cx":int(center_x_light/scaling_x), # center x light
                "cy":int((scaling_height-center_y_light)/scaling_y), # center y light
                "target_x":int(center_x/scaling_x), #  center x frame
                "target_y":int(center_y/scaling_y), #  center y frame
                "kp":kp,
                "ki":ki,
                "kd":kd,
                "max_speed":setting_data['control_speed_distance']['speed_screw'],
                "off_set":off_set,
                "status": status
            }
        
        print(payload)
        print(self.helio_stats_id_endpoint)
        headers = {
            'Content-Type': 'application/json'  
        }

        try:
            response = requests.post("http://"+self.helio_stats_id_endpoint+"/auto-data", data=json.dumps(payload), headers=headers, timeout=5)
            print("=== DEBUG AUTO ===")
            print("End point => ","http://"+self.helio_stats_id_endpoint+"/auto-data")
            print("payload => ",payload)
            print("reply status => ",response.status_code)
            print("\n")
            if response.status_code != 200:
                try:
                    error_info = response.json()
                    self.show_popup("Connection Error", f"{str(error_info)} \n auto mode off")
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                except ValueError:
                    self.show_popup("Connection Error", f"{str(response.text)} \n auto mode off")
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
            else:
                print("debug send success! ",response)

        except Exception as e:
            self.show_popup("Connection Error", f"{str(e)} \n auto mode off")
            self.turn_on_auto_mode = False
            self.ids.label_auto_mode.text = "Auto off"
            self.__off_loop_auto_calculate_diff() 

    def __haddle_save_positon(self,timestamp,helio_stats_id,camera_use,id,currentX, currentY,err_posx,err_posy,x,y,x1,y1,ls1,st_path,move_comp,elevation,azimuth):
        adding_time = {
            "timestamp": timestamp,
            "helio_stats_id": helio_stats_id,
            "camera_use": camera_use,
            "id": id,
            "currentX":  currentX,
            "currentY": currentY,
            "err_posx": err_posx,
            "err_posy": err_posy,
            "x": x,
            "y": y,
            "x1": x1,
            "y1": y1, 
            "ls1": ls1,
            "st_path": st_path,
            "move_comp": move_comp,
            "elevation": elevation,
            "azimuth": azimuth,
            "control_by": "machine"
        }

        filename = "./data/result/error_data.csv"
        filepath = os.path.join(os.getcwd(), filename)
        try:
            fieldnames = adding_time.keys()
            with open(filepath, mode='a', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writerow(adding_time)
                self.show_popup("Finish", f"Auto mode off")
                self.turn_on_auto_mode = False
                self.ids.label_auto_mode.text = "Auto off"
                self.__off_loop_auto_calculate_diff()
        except Exception as e:
            self.turn_on_auto_mode = False
            self.ids.label_auto_mode.text = "Auto off"
            self.__off_loop_auto_calculate_diff()
            self.show_popup(f"Error saving file:\n{str(e)}")    

    def haddle_extact_boarding_frame(self):
        data = self.bounding_box_frame_data.text
        numbers = re.findall(r'\d+', data)
        int_numbers = [int(num) for num in numbers]
        return int_numbers[0], int_numbers[1], int_numbers[2], int_numbers[3]

    def haddle_convert_to_old_resolution(self,current_width, current_height):
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            print(e)
            self.show_popup("Error get setting", f"Failed to get value in setting file: {e}")
        
        # is_scale = current_width / current_height  
        # scaling_x = round((setting_data['old_frame_resolution']['width'] / is_scale),2) 
        # scaling_y = round((setting_data['old_frame_resolution']['height'] / is_scale),2)
        # return scaling_x, scaling_y 

        scaling_x = round((current_width/setting_data['old_frame_resolution']['width']),2) 
        scaling_y = round((current_height/setting_data['old_frame_resolution']['height']),2)

        return scaling_x, scaling_y, current_height
    