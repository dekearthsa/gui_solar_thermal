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
# from ..controller.crud_data import CrudData

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
        self.fail_url = [] # "192.168.0.1","192.168.0.2","192.168.0.2","192.168.0.2","192.168.0.2","192.168.0.2"
        self.list_fail_set_origin = [] # {"url": "102", "origin": "x"},{"url": "102", "origin": "x"}

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
        
    def show_popup_continued(self, title, message, action):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text=message)
        layout.add_widget(label)
        grid = GridLayout(cols=1, size_hint=(1,1) ,height=30)
        if action == "to-origin":
            button_con = Button(text="continue set origin")
            button_con.bind(on_release=partial(self.handler_set_origin))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup = Popup(title=title,
                        content=layout,
                        size_hint=(None, None), size=(400, 200))
            popup.open()
        if action == "to-auto":
            button_con = Button(text="continue auto start")
            button_con.bind(on_release=partial(self.handler_set_origin))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup = Popup(title=title,
                        content=layout,
                        size_hint=(None, None), size=(400, 200))
            popup.open()

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

    def handler_checking_connection(self, list_conn):  ## data from connection.json {}
        print("checking connection helio stats....")
        for el in list_conn['helio_stats_ip']:
            while i < self.time_loop_update:
                result = requests.get(url="http://"+el['ip'], timeout=3)
                payload = {
                    "url": el['ip']
                }
                if result.status_code == 200:
                    CrudData.save_standby(payload)
                    self.standby_url.append(payload)
                    break
                else:
                    i += 1
                    if i >= self.time_loop_update:
                        CrudData.save_pending(payload)
                        self.pending_url.append(payload)
        if len(self.pending_url) > 0:
            self.handler_reconn_pending()
        print("checking connection helio stats done!")

    def handler_reconn_pending(self):
        print("checking reconnect pending...")
        for url in self.pending_url:
            result = requests.get(url="http://"+url['url'], timeout=3)
            payload = {
                "url": url['url']
            }
            if result.status_code == 200:
                self.standby_url.append(payload)
            else:
                self.fail_url.append(payload)
        self.pending_url = []
        print("done checking reconnect pending.")

    def handler_set_origin(self):
        # fail_list_origin = []
        try:
            for url in self.standby_url:
                set_origin_x = {"topic": "origin", "axis": "x", "speed":400} 
                set_origin_y = {"topic": "origin", "axis": "y", "speed":400} 
                result_x = requests.post("http://"+url['url']+"/update-data", json=set_origin_x, timeout=5)
                if result_x.status_code != 200:
                    payload = {
                        "url": url['url'],
                        "origin": "x"
                    }
                    # fail_list_origin.append(payload)
                    self.list_fail_set_origin.append(payload)
                    # self.show_popup("Error connection", f"connection timeout {url['url']}")

                result_y = requests.post("https://"+url['url']+"/update-data", json=set_origin_y, timeout=5)
                if result_y.status_code != 200:
                    payload = {
                        "url": url['url'],
                        "origin": "y"
                    }
                    # fail_list_origin.append(payload)
                    self.list_fail_set_origin.append(payload)
                    # self.show_popup("Error connection", f"connection timeout {url}")
            if len(self.list_fail_set_origin) > 0:
                CrudData.save_origin(self.list_fail_set_origin)
                self.show_popup("warning", "Number of origin fail " +f"{len(self.list_fail_set_origin)}")
        except Exception as e:
            print("error handler_set_origin func " + f"{e}")
            self.show_popup("Error connection",f"connection timeout {e}")

    def handler_get_current_pos(self):
        try:
            list_url = CrudData.open_list_connection()
            standby_json = CrudData.read_standby()
            pending_json = CrudData.read_pending()
            fail_conn_json = CrudData.read_fail_conn()

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
                        # CrudData.read_standby(payload)
                        self.standby_url.append(payload)
                    else:
                        payload = {"url": url}
                        pending_json.append(payload)
                        # CrudData.read_pending(payload)
                        self.pending_url.append(payload)
                except Exception as req_error:
                    print(f"Error connecting to {url}: {req_error}")
                    pending_json.append({"url": url})
            
            if len(self.pending_url) > 0:
                for url in self.pending_url:
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
                            self.pending_url.remove(url)
                            pending_json.remove(url)
                            self.standby_url.append(payload)

                            with open("./data/standby_conn/pending.json", 'w') as update_pending_file:
                                json.dump(pending_json, update_pending_file)
                        else:
                            payload = {"url": url}
                            fail_conn_json.append(payload)
                            # CrudData.save_fail_conn(payload)
                            self.fail_url.append(payload)
                    except Exception as req_error:
                        print(f"Error connecting to {url}: {req_error}")
                        payload = {"url": url}
                        fail_conn_json.append(payload)
                        # CrudData.save_fail_conn(payload)
                        self.fail_url.append(payload)

            CrudData.update_standby(standby_json)
            CrudData.update_pending(pending_json)
            CrudData.update_failconn(fail_conn_json)

        except Exception as e:
            print(f"Error in handler_get_current_pos: {e}")


    def handler_loop_checking(self):
        if self.is_loop_mode == True:
            self.handler_get_current_pos()
            if len(self.fail_url) > 0:
                self.show_popup_continued(title="Warning",  message=f"Number heliostats disconnected {len(self.fail_url)}", action="to-origin")
            else:
                self.handler_set_origin()
        else:
            self.handler_setup_without_loop_mode()
        

    def handler_setup_without_loop_mode(self):
        # if self.is_loop_mode == True:
            list_conn = CrudData.open_list_connection()
            if len(list_conn) >= 1:
                self.handler_checking_connection(list_conn)
                # self.handler_reconn_pending()
                if len(self.fail_url) > 0:
                    self.show_popup_continued(title="Warning",  message=f"Number heliostats disconnected {len(self.fail_url)}", action="to-origin")
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

    def re_set_origin(self,payload):
        try:
            payload = {
                "topic":"origin",
                "axis": payload['origin'],
                "speed": 400
            }
            result = requests.get("http://"+payload['url']+"/update-data", json=payload, timeout=5)
            if result.status_code != 200:
                self.show_popup("Error origin", "Error set origin\n" +"axis " + f"{payload['origin']}" + " ip:"+f"{payload['url']}" )
        except Exception as e:
            print("error re_set_origin func => " + f"{e}")
            self.show_popup("Error connection", f"{payload} error connection!")

    def handler_check_origin(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        for url in self.list_fail_set_origin:
            grid = GridLayout(cols=2, size_hint=(1,1), height=40, spacing=10)
            label = Label(text=str(url), size_hint=(0.3,1))
            button_origin_set = Button(text="SET", size_hint=(0.2,1))
            button_origin_set.bind(on_release=partial(self.re_set_origin, url))
            grid.add_widget(label)
            grid.add_widget(button_origin_set)
            layout.add_widget(grid)

        popup = Popup(
            title="Fail set origin list",
            content=layout,
            size_hint=(None, None),
            size=(1050, 960),
            auto_dismiss=True
        )

        popup.open()








class CrudData:
    def __init__(
            self,
            path_standby_json="./data/setting/standby.json",
            path_pending_json="./data/setting/pending.json",
            path_fail_json="./data/setting/failconn.json",
            path_setting_json="./data/setting/setting.json",
            path_connection_json="./data/setting/connection.json",
            path_origin_json="./data/standby_conn/origin_fail.json"
    ):
        self.path_standby_json = path_standby_json
        self.path_pending_json = path_pending_json
        self.path_fail_json = path_fail_json
        self.path_setting_json = path_setting_json
        self.path_connection_json = path_connection_json
        self.path_origin_json = path_origin_json

    def open_list_connection(self):
        print("open list helio stats conn...")
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
                list_conn = storage['helio_stats_ip']
                return list_conn
        except Exception as e:
            print("Error ")

    def read_pending(self):
        print("open read pending...")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read pending.json " + f"{e}")
        print("done read pending.")

    def read_fail_conn(self):
        print("open read fail_conn...")
        try:
            with open('./data/standby_conn/failconn.json', 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read failconn.json " + f"{e}")
        print("done read fail_conn.")

    def read_standby(self):
        print("open read standby...")
        try:
            with open('./data/standby_conn/standby.json', 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read standby.json " + f"{e}")
        print("done read standby.")

    def save_pending(self, url):
        
        print("save pending ip helio stats....")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                list_pending = json.load(file)
                list_pending.append(url)
            with open('./data/standby_conn/pending.json', 'w') as file_save:
                json.dump(list_pending, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save pending: {e}")
        print("done save pending ip helio stats.")

    def save_standby(self, url):
        print("save ip helio stats....")
        try:
            with open('./data/standby_conn/standby.json', 'r') as file:
                list_standby = json.load(file)
                list_standby.append(url)
            with open('./data/standby_conn/standby.json', 'w') as file_save:
                json.dump(list_standby, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save standby: {e}")
        print("done save ip helio stats.")

    def save_fail_conn(self, url):
        print("save ip helio stats....")
        try:
            with open('./data/standby_conn/failconn.json', 'r') as file:
                list_failconn = json.load(file)
                list_failconn.append(url)
            with open('./data/standby_conn/failconn.json', 'w') as file_save:
                json.dump(list_failconn, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save failconn: {e}")
        print("done save ip helio stats.")

    def remove_by_id_pending(self, url):
        print("remove pending...")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != url['url']]

            with open('./data/standby_conn/pending.json', 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read pending.json file" + f"{e}")

    def remove_by_id_standby(self, url):
        print("remove standby.json...")
        try:
            with open('./data/standby_conn/standby.json', 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != url['url']]

            with open('./data/standby_conn/standby.json', 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read standby.json file" + f"{e}")

    def remove_by_id_fail_conn(self, url):
        print("remove failconn.json...")
        try:
            with open('./data/standby_conn/failconn.json', 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != url['url']]

            with open('./data/standby_conn/failconn.json', 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read failconn.json file" + f"{e}")

    def update_standby(self, payload):
        print("update stanby...")
        try:
            with open("./data/standby_conn/standby.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file update_standby " + f"{e}")
        print("update finish.") 

    def update_pending(self, payload):
        print("update pending...")
        try:
            with open("./data/standby_conn/pending.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file pending " + f"{e}")
        print("update finish.")

    def update_failconn(self, payload):
        print("update failconn...")
        try:
            with open("./data/standby_conn/failconn.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file failconn " + f"{e}")
        print("update finish.")

    def read_fail_origin(self):
        print("read origin...")
        try:
            with open(self.path_origin_json, 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read_fail_origin " + f"{e}")
        print("read finish.")

    def save_origin(self, payload):
        print("Save origin is fail.")
        try:
            with open(self.path_origin_json, 'w') as file:
                json.dump(payload, file)
        except Exception as e:
            print("Error save_origin" + f"{e}")
        print("Finish origin is fail.")

    def update_origin(self, payload):
        print("update origin...")
        try:
            with open(self.path_origin_json, 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file failconn " + f"{e}")
        print("update finish")

    def remove_by_id_origin(self, payload):
        print("remove origin by id...")
        try:
            with open(self.path_origin_json, 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != payload['url']]

            with open(self.path_origin_json, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read failconn.json file" + f"{e}") 
        print("remove finish.")