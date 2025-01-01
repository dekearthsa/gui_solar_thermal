from kivy.uix.actionbar import Button
from kivy.uix.gridlayout import GridLayout
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
from functools import partial
class ControllerAuto(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.demo_timeout_reply = 2
        self.is_loop_mode = False
        self.helio_stats_id_endpoint = "" ### admin select helio stats endpoint
        self.helio_stats_selection_id = "" ####  admin select helio stats id
        self.camera_endpoint = ""
        self.camera_selection = ""
        self.turn_on_auto_mode = False
        self.is_frist_time_open = True
        self.pending_url = []
        self.standby_url = []
        self.fail_url = ["192.168.0.1","192.168.0.2"]

        self.speed_screw = 1
        self.distance_mm = 1 
        self.is_auto_on = False
        self.static_title_mode = "Auto menu || Camera status:On"
        self.array_helio_stats = []
        self.time_loop_update = 5 ## 2 sec test update frame
        self.stop_move_helio_x_stats = 8 ### Stop move axis x when diff in theshold
        self.stop_move_helio_y_stats = 8 ### Stop move axis y when diff in theshold

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

            return h_id, c_id
        except Exception as e:
            self.show_popup("Error", f"{e}")

    def open_list_connection(self):
        print("open list helio stats conn...")
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
                list_conn = storage['helio_stats_ip']
                return list_conn
        except Exception as e:
            self.show_popup("Error", f"{e}")

    def save_pending(self, url):
        print("save pending ip helio stats....")
        try:
            with open('./data/setting/pending.json', 'r') as file:
                list_pending = json.load(file)
                list_pending.append(url)
            with open('./data/setting/pending.json', 'w') as file_save:
                json.dump(list_pending, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save pending: {e}")
        print("done save pending ip helio stats.")

    def save_standby(self, url):
        print("save ip helio stats....")
        try:
            with open('./data/setting/standby.json', 'r') as file:
                list_standby = json.load(file)
                list_standby.append(url)
            with open('./data/setting/standby.json', 'w') as file_save:
                json.dump(list_standby, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save standby: {e}")
        print("done save ip helio stats.")

    def handler_checking_connection(self, list_conn):
        print("checking connection helio stats....")
        for el in list_conn:
            while i < self.time_loop_update:
                payload = requests.get(url="http://"+el['ip'], timeout=3)
                if payload.status_code == 200:
                    self.save_standby(el)
                    self.standby_url.append(el)
                    break
                else:
                    i += 1
                    if i >= self.time_loop_update:
                        self.save_pending(el)
                        self.pending_url.append(el)
        print("checking connection helio stats done!")

    def handler_reconn_pending(self):
        print("checking reconnect pending...")
        for url in self.pending_url:
            payload = requests.get(url="http://"+url, timeout=3)
            if payload.status_code == 200:
                self.standby_url.append(url)
            else:
                self.fail_url.append(url)
        self.pending_url = []
        print("done checking reconnect pending.")

    def handler_set_origin(self):
        try:
            for url in self.standby_url:
                set_origin_x = {"topic": "origin", "axis": "x", "speed":400} 
                set_origin_y = {"topic": "origin", "axis": "y", "speed":400} 
                result_x = requests.post("http://"+url+"/update-data", json=set_origin_x, timeout=5)
                if result_x.status_code != 200:
                    self.show_popup("Error connection", f"connection timeout {url}")
                
                result_y = requests.post("https://"+url+"/update-data", json=set_origin_y, timeout=5)
                if result_y.status_code != 200:
                    self.show_popup("Error connection", f"connection timeout {url}")

        except Exception as e:
            print("error handler_set_origin func " + f"{e}")
            self.show_popup("Error connection",f"connection timeout {url}")

    def handler_get_current_pos(self):
        try:
            with open('./data/setting/connection.json', 'r') as file:
                list_url = json.load(file)
            with open("./data/standby_conn/standby.json", 'r') as raw_standby:
                standby_json = json.load(raw_standby)

            with open("./data/standby_conn/pending.json", 'r') as raw_pending:
                pending_json = json.load(raw_pending)

            for url in list_url:
                try:
                    result = requests.get("http://" + url, timeout=3)
                    setJson = result.json()

                    if result.status_code == 200:
                        payload = {
                            "url": url,
                            "current_x": setJson['currentX'],
                            "current_y": setJson['currentY']
                        }
                        standby_json.append(payload)
                    else:
                        payload = {"url": url}
                        pending_json.append(payload)
                except Exception as req_error:
                    print(f"Error connecting to {url}: {req_error}")
                    pending_json.append({"url": url})

            # Write back the updated data to files
            with open("./data/standby_conn/standby.json", 'w') as write_file:
                json.dump(standby_json, write_file, indent=4)

            with open("./data/standby_conn/pending.json", 'w') as write_file:
                json.dump(pending_json, write_file, indent=4)

        except Exception as e:
            print(f"Error in handler_get_current_pos: {e}")


    def handler_loop_checking(self):
        if self.is_loop_mode == True:
            self.handler_get_current_pos()
        else:
            self.handler_auto_mode_setup()
        

    def handler_auto_mode_setup(self):
        # if self.is_loop_mode == True:
            list_conn = self.open_list_connection()
            if len(list_conn) >= 1:
                self.handler_checking_connection(list_conn)
                self.handler_reconn_pending()
                if len(self.fail_url) > 0:
                    count_disconn = len(self.fail_url)
                    self.show_popup("Warning", f"Heliostats disconnect {count_disconn} ip.")
                else:
                    self.handler_set_origin()
            else:
                self.show_popup("Alert", "Not found any helio stats!")
        # else:
        #     pass

    def active_auto_mode(self):
        h_id, _ = self.selection_url_by_id()
        if self.camera_endpoint != "" and self.helio_stats_id_endpoint != "":
            if self.status_auto.text == self.static_title_mode:
                if self.turn_on_auto_mode == False:
                    if int(self.number_center_light.text) == 1:
                        self.turn_on_auto_mode = True
                        self.helio_stats_selection_id = h_id
                        self.ids.label_auto_mode.text = "Auto on"
                        self.update_loop_calulate_diff(1)
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
                path_time_stamp = now.strftime("%d_%m_%y")
                if abs(center_x - target_x) <= self.stop_move_helio_x_stats and abs(center_y - target_y) <= self.stop_move_helio_y_stats:
                    # try:
                        # with open('./data/setting/setting.json', 'r') as file:
                        #     setting_data = json.load(file)
                        payload = requests.get(url="http://"+self.helio_stats_id_endpoint)
                        # print("payload => ", payload)
                        setJson = payload.json()
                        # print(setJson)
                        # setJson = json.dumps(payload)
                        self.__haddle_save_positon(
                            timestamp=timestamp,
                            pathTimestap=path_time_stamp,
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
            self.__off_loop_auto_calculate_diff()
            self.turn_on_auto_mode = False
            self.ids.label_auto_mode.text = "Auto off"
            self.show_popup("Alert", "Camera is offline.")

    def __on_loop_auto_calculate_diff(self):
        # if self.is_frist_time_open == True:
        
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
                "max_speed":setting_data['control_speed_distance']['auto_mode']['speed'],
                "off_set":off_set,
                "status": status
            }

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

    def __haddle_save_positon(self,timestamp,pathTimestap,helio_stats_id,camera_use,id,currentX, currentY,err_posx,err_posy,x,y,x1,y1,ls1,st_path,move_comp,elevation,azimuth):
        with open('./data/setting/setting.json', 'r') as file:
            storage = json.load(file)

        adding_time = {
            "timestamp": timestamp,
            "helio_stats_id": helio_stats_id,
            "camera_use": storage['storage_endpoint']['camera_ip']['id'],
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


        now = datetime.now()
        path_time_stamp = now.strftime("%d_%m_%y"+"_"+helio_stats_id)
        timing =  now.strftime("%H:%M:%S")
        adding_path_data = {
            "timestamp": timing,
            "x":  currentX,
            "y": currentY,
        }
        
        json_str = json.dumps(adding_path_data)
        perfixed_json = f"*{json_str}"

        if storage['storage_endpoint']['camera_ip']['id'] == "camera-bottom":
            filename = "./data/calibrate/result/error_data.csv"
            path_file_by_date = f"./data/calibrate/result/{path_time_stamp}/data.txt"
            path_folder_by_date = f"./data/calibrate/result/{path_time_stamp}"
            filepath = os.path.join(os.getcwd(), filename)
            filepath_by_date = os.path.join(os.getcwd(), path_folder_by_date)
            check_file_path = os.path.isdir(filepath_by_date)
            try:
                fieldnames = adding_time.keys()
                with open(filepath, mode='a', newline='', encoding='utf-8') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writerow(adding_time)

                if check_file_path == False:
                    os.mkdir(path_folder_by_date)
                    with open(path_file_by_date, mode='w', newline='') as text_f:
                        text_f.write(perfixed_json+"\n")
                    self.show_popup("Finish", f"Auto mode off")
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                else:
                    with open(path_file_by_date, mode='a', newline='', encoding='utf-8') as text_f:
                        text_f.write(perfixed_json+"\n")
                    self.show_popup("Finish", f"Auto mode off")
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
            except Exception as e:
                self.turn_on_auto_mode = False
                self.ids.label_auto_mode.text = "Auto off"
                self.__off_loop_auto_calculate_diff()
                self.show_popup("Error",f"Error saving file:\n{str(e)}")  

        else:
            filename = "./data/receiver/result/error_data.csv"
            path_file_by_date = f"./data/receiver/result/{path_time_stamp}/data.txt"
            path_folder_by_date = f"./data/receiver/result/{path_time_stamp}"
            filepath = os.path.join(os.getcwd(), filename)
            filepath_by_date = os.path.join(os.getcwd(), path_folder_by_date)
            check_file_path = os.path.isdir(filepath_by_date)
            try:
                fieldnames = adding_time.keys()
                with open(filepath, mode='a', newline='', encoding='utf-8') as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writerow(adding_time)

                if check_file_path == False:
                    os.mkdir(path_folder_by_date)
                    with open(path_file_by_date, mode='w', newline='') as text_f:
                        text_f.write(perfixed_json+"\n")
                    self.show_popup("Finish", f"Auto mode off")
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                else:
                    with open(path_file_by_date, mode='a', newline='', encoding='utf-8') as text_f:
                        text_f.write(perfixed_json+"\n")
                    self.show_popup("Finish", f"Auto mode off")
                    self.turn_on_auto_mode = False
                    self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                    
            except Exception as e:
                self.turn_on_auto_mode = False
                self.ids.label_auto_mode.text = "Auto off"
                self.__off_loop_auto_calculate_diff()
                self.show_popup("Error",f"Error saving file:\n{str(e)}")  

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
    
        scaling_x = round((current_width/setting_data['old_frame_resolution']['width']),2) 
        scaling_y = round((current_height/setting_data['old_frame_resolution']['height']),2)

        return scaling_x, scaling_y, current_height

    def active_loop_mode(self):
        if self.is_loop_mode == False:
            self.is_loop_mode = True
        else:
            self.is_loop_mode = False

    def list_fail_connection(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        for url in self.fail_url:
            grid = GridLayout(cols=2, size_hint=(1,1),height=40,spacing=10)
            label = Label(text=url, size_hint=(0.3,1))
            button_reconn = Button(text="Reconnect", size_hint=(0.2,1))
            button_reconn.bind(on_release=partial(self.handler_reconn_helio, url))
            grid.add_widget(label)
            grid.add_widget(button_reconn)
            layout.add_widget(grid)
        
        popup = Popup(
            title="Reconnection list",
            content=layout,
            size_hint=(None, None),
            size=(1050, 960),
            auto_dismiss=True  # Allow dismissal by clicking outside or pressing Escape
        )
        popup.open()

    def handler_reconn_helio(self, url, instance):
        try:
            payload = requests.get(url="http://"+url, timeout=3)
            if payload.status_code == 200:
                self.fail_url.remove(url)
                self.standby_url.append(url)
                self.show_popup("connected", f"{url} is connected.")
            else:
                self.show_popup("connection timeout", f"{url} connection timeout")
        except Exception as e:
            print("error handler_reconn_helio func " + f"{e}")
            self.show_popup("Error", "Error in handler_reconn_helio\n" + f"{e}")


        ### debug mode ###
        # self.fail_url.remove(url)
        