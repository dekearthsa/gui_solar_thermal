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

        # Clock.schedule_once(lambda dt: self.fetch_helio_stats_list())
        self.speed_screw = 1
        self.distance_mm = 1 
        self.is_auto_on = False
        self.static_title_mode = "Auto menu || Camera status:On"
        self.array_helio_stats = []
        self.time_loop_update = 2 ## 2 sec test update frame
        self.stop_move_helio_x_stats = 2 ### Stop move axis x when diff in theshold
        self.stop_move_helio_y_stats = 2 ### Stop move axis y when diff in theshold
        self.static_get_api_helio_stats_endpoint = "http://localhost:8888/demo/get"

    # def fetch_helio_stats_list(self):
    #     self.ids.helio_stats_operate.text = self.helio_stats_id.text
    #     self.ids.camera_selection.text = self.camera_url_id.text


    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(400, 200))
        popup.open()

    ### camera endpoint debug ###
    def selection_url_by_id(self):
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
            
            h_id = self.__extract_coordinates_helio_stats_loop_checking(self.helio_stats_id.text)
            c_id = self.__extract_coordinates_helio_stats_loop_checking(self.camera_url_id.text)

            for helio_data in storage['helio_stats_ip']:
                if h_id == helio_data['id']:
                    self.helio_stats_id_endpoint = helio_data['ip']
                    break

            for camera_data in storage['camera_url']:
                if c_id == camera_data['id']:
                    self.camera_endpoint = camera_data['url']
                    break
        except Exception as e:
            self.show_popup("Error", f"{e}")

    def active_auto_mode(self):
        self.selection_url_by_id()
        if self.camera_endpoint != "" and self.helio_stats_id_endpoint != "":
            if self.status_auto.text == self.static_title_mode:
                if self.turn_on_auto_mode == False:
                    self.turn_on_auto_mode = True
                    self.helio_stats_selection_id = self.helio_stats_id.text.split(": ")[1]
                    self.ids.label_auto_mode.text = "Auto on"
                    self.__on_loop_auto_calculate_diff()
                else:
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
            else: 
                self.show_popup("Alert", f"Please turn on camera.")
        else:
            self.show_popup("Alert", f"Please select helio stats id and camera")

    def update_loop_calulate_diff(self, dt):
        current_helio_stats = self.__extract_coordinates_helio_stats_loop_checking(self.helio_stats_id.text)
        center_x, center_y, target_x, target_y = self.__extract_coordinates_pixel(self.center_frame_auto.text, self.center_target_auto.text)
        if self.status_auto.text == self.static_title_mode:
            if current_helio_stats == self.helio_stats_selection_id:
                now = datetime.now()
                timestamp = now.strftime("%d/%m/%y %H:%M:%S")
                if (center_x - target_x) <= self.stop_move_helio_x_stats and (center_y - target_y) <= self.stop_move_helio_y_stats:
                    try:
                        payload = requests.get(url=self.static_get_api_helio_stats_endpoint)
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
                        axis="x,y",
                        center_x=center_x,
                        center_y=center_y,
                        target_y=target_y,
                        target_x=target_x,
                        kp=1,
                        ki=1,
                        kd=2,
                        max_speed=200,
                        off_set=1,
                        status="1"
                        )
            else:
                self.show_popup("Alert", f"Helio stats endpoint have change!")
                self.helio_stats_selection_id = current_helio_stats
                if (center_x - target_x) <= self.stop_move_helio_x_stats and (center_y - target_y) <= self.stop_move_helio_y_stats:
                    try:
                        payload = requests.get(url=self.static_get_api_helio_stats_endpoint)
                        setJson = json.dumps(payload)
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
                        axis="x,y",
                        center_x=center_x,
                        center_y=center_y,
                        target_y=target_y,
                        target_x=target_x,
                        kp=1,
                        ki=1,
                        kd=2,
                        max_speed=200,
                        off_set=1,
                        status="1"
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

    def __extract_coordinates_helio_stats_loop_checking(self, helio_id):
        return helio_id.split(": ")[1]
    
    # def __extract_coordinates_camera_loop_checking(self, camera_id):


    def __extract_coordinates_pixel(self, s1, s2): ##(frame_center, target_center)
        pattern = r'X:\s*(\d+)px\s*Y:\s*(\d+)px'
        match = re.search(pattern, s1)
        match_2 = re.search(pattern, s2)

        if match:   
            if match_2:
                center_x = int(match.group(1))
                target_x = int(match_2.group(1))
                
                center_y = int(match.group(2))
                target_y = int(match_2.group(2))
                # diff_x = int(match.group(1)) - int(match_2.group(1))
                # diff_y = int(match.group(2)) - int(match_2.group(2))
                return center_x, center_y, target_x, target_y
        else:
            print("The string format is incorrect.")

    def __send_payload(self, axis,center_x, center_y,target_x,target_y,kp,ki,kd,max_speed,off_set,status):
        payload = {
                "topic":"auto",
                "axis": axis,
                "cx":center_x,
                "cy":center_y,
                "target_x":target_x,
                "target_y":target_y,
                "kp":kp,
                "ki":ki,
                "kd":kd,
                "max_speed":max_speed,
                "off_set":off_set,
                "status": status
            }
        headers = {
            'Content-Type': 'application/json'  
        }
        
        try:
            response = requests.post(self.helio_stats_id_endpoint, data=json.dumps(payload), headers=headers)
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