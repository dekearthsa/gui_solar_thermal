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
from controller.crud_data import CrudData
from controller.control_origin import ControlOrigin
from controller.control_get_current_pos import ControlGetCurrentPOS
from controller.control_check_conn_heliostats import ControlCheckConnHelioStats
from controller.control_heliostats import ControlHelioStats
# from command.manual_command import ControllerManual

class ControllerAuto(BoxLayout):
    def __init__(self,**kwargs ):
        
        super().__init__(**kwargs)

        self.is_loop_mode = False
        self.helio_stats_id_endpoint = "" ### admin select helio stats endpoint
        self.helio_stats_selection_id = "" ####  admin select helio stats id
        self.camera_endpoint = ""
        self.camera_selection = ""
        self.turn_on_auto_mode = False
        self.pending_url = []
        self.standby_url = []
        
        self.status_finish_loop_mode_first = False
        self.static_title_mode = "Auto menu || Camera status:On"
        self.time_loop_update = 5 ## 2 sec test update frame
        self.time_check_light_update = 1
        self.stop_move_helio_x_stats = 8 ### Stop move axis x when diff in theshold
        self.stop_move_helio_y_stats = 8 ### Stop move axis y when diff in theshold
        self.set_axis = "x"
        self.set_kp = 1
        self.set_ki = 1
        self.set_kd = 2
        self.set_max_speed = 100
        self.set_off_set = 1
        self.set_status ="1"
        self._light_check_result = False
        self.fail_checking_light_desc = {}
        self.fail_checking_light = False

        self.helio_stats_fail_light_checking = ""
        self.__light_checking_ip_operate = ""
        self.fail_url = [] # "192.168.0.1","192.168.0.2","192.168.0.2","192.168.0.2","192.168.0.2","192.168.0.2"
        self.list_fail_set_origin = [] # {"ip": "192.168.0.1", "origin": "x"},{"ip": "192.168.0.2", "origin": "x"}
        self.list_success_set_origin = []
        self.list_success_set_origin_store = []
        self.list_origin_standby = []
        self.list_pos_move_out = []
        self.current_helio_index = 0
        self._on_check_light_timeout_event = None
        self.path_data_heliostats = []
        self.path_data_not_found_list = []
        self.operation_type_selection = ""
        self.debug_counting = 0

    def show_popup_continued(self, title, message ,action):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text=message)
        layout.add_widget(label)
        grid = GridLayout(cols=1, size_hint=(1,1) ,height=30)
        popup = Popup(title=title,
                        content=layout,
                        size_hint=(None, None), size=(1000, 500))
        if action == "to-origin":
            button_con = Button(text="continue set origin")
            button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            
            popup.open()

        elif action == "to-auto":
            button_con = Button(text="continue auto start")
            button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup.open()

        elif action == "to-checking-light":
            button_con = Button(text="continue auto start")
            button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup.open()

        elif action == "try-again":
            button_con = Button(text="try again")
            button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup.open()
        elif action == "to-process-next-helio":
            button_con = Button(text="continue")
            button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup.open()

    def close_popup_and_continue(self, popup, process):
        popup.dismiss() 
        if process == "to-origin":
            self.handler_set_origin() 
        elif process == "to-checking-light":
            self.handle_checking_light()
        elif process == "to-auto":
            self.handler_set_origin()
        elif process == "try-again":
            self.handle_checking_light()
        elif process == "to-process-next-helio":
            self.process_next_helio()


    def show_popup_with_ignore_con(self, title, message, h_data, action):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text=message)
        layout.add_widget(label)
        grid = GridLayout(cols=2, size_hint=(1,1) ,height=30)

        if action == "try-again":
            button_ignore = Button(text="Ignore and continue")
            button_ignore.bind(on_release=lambda instance: self.__ignore_failure_checking_light_function(h_data=h_data))
            grid.add_widget(button_ignore)

            button_con = Button(text="try again")
            button_con.bind(on_release=lambda instance: self.handle_checking_light())
            grid.add_widget(button_con)
            layout.add_widget(grid)

            popup = Popup(title=title,
                        content=layout,
                        size_hint=(None, None), size=(1000, 500))
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

    def checking_light_in_target(self,dt=None):
        print("start check light result " +  self.__light_checking_ip_operate + " light detect = " +self.number_center_light.text)
        self.ids.logging_process.text = "Start check light result in target."
        ### production need to > 0 ###
        if int(self.number_center_light.text) == 0: ### for debug mode ### 
        # if int(self.number_center_light.text) > 0:
            status = ControlHelioStats.stop_move(self,ip=self.__light_checking_ip_operate)
            if status:
                self._light_check_result = True
                self.__off_loop_checking_light()
                
            else:
                self.show_popup("Error connection", "Error connection ip" + f"{self.__light_checking_ip_operate}")

    def __off_loop_checking_light(self, dt=None):
        Clock.unschedule(self.checking_light_in_target)
        Clock.unschedule(self._on_check_light_timeout_event)
        ### change this to active_auto_mode for production ### 
        self.__debug_on_active_auto_mode_debug()
        ### production ###
        # self.active_auto_mode()

    def process_next_helio(self, dt=None):
        # Check if we are done with all heliostats
        if self.status_finish_loop_mode_first == False:
            print("Loop using function use path.")
            self.ids.logging_process.text = "Loop using function use path."
            if self.current_helio_index >= len(self.path_data_heliostats):
                # All done
                if self.is_loop_mode:
                    self.current_helio_index = 0
                    self.list_fail_set_origin = self.path_data_heliostats
                else:
                    self._finish_auto_mode()
                    return
            
            h_data = self.path_data_heliostats[self.current_helio_index]
            
            # 2. Send nearest time data
            result = ControlHelioStats.find_nearest_time_and_send(
                self, list_path_data=h_data['path'], ip=h_data['ip']
            )
            if result['is_fail']:
                # Fail to send => show error, store fail, break the entire process
                self.fail_checking_light_desc = {
                    "title": "Error send path",
                    "message": "Fail to nearest path time to heliostats",
                }
                self.fail_checking_light = True
                self.helio_stats_fail_light_checking = h_data
                self._handle_fail()
                return
            
            # 3. Start checking the light
            print(f"Start auto mode. ip = {h_data['ip']}")
            self._light_check_result = False
            self.__light_checking_ip_operate = h_data['ip']
            
            # Schedule checking_light_in_target periodically
            Clock.schedule_interval(self.checking_light_in_target, self.time_check_light_update)
            
            # Schedule a timeout in 30 seconds to evaluate the result
            self._on_check_light_timeout_event = Clock.schedule_once(self._on_check_light_timeout, 10)
        else:
            print("Debug loop using function move in heliostats.")
            self.ids.logging_process.text = "Debug loop using function move in heliostats."
            if self.current_helio_index >= len(self.path_data_heliostats):
                # All done
                if self.is_loop_mode:
                    self.current_helio_index = 0
                    self.list_fail_set_origin = self.path_data_heliostats
                else:
                    self._finish_auto_mode()
                    return
            
            h_data = self.path_data_heliostats[self.current_helio_index]
            
            # 2. Send nearest time data
            result = ControlHelioStats.move_helio_in(
                self, ip=h_data['ip']
            )
            if result['is_fail']:
                # Fail to send => show error, store fail, break the entire process
                self.fail_checking_light_desc = {
                    "title": "Error send path",
                    "message": "Fail to nearest path time to heliostats",
                }
                self.fail_checking_light = True
                self.helio_stats_fail_light_checking = h_data
                self._handle_fail()
                return
            
            # 3. Start checking the light
            print(f"Start auto mode. ip = {h_data['ip']}")
            self._light_check_result = False
            self.__light_checking_ip_operate = h_data['ip']
            
            # Schedule checking_light_in_target periodically
            Clock.schedule_interval(self.checking_light_in_target, self.time_check_light_update)
            
            # Schedule a timeout in 30 seconds to evaluate the result
            self._on_check_light_timeout_event = Clock.schedule_once(self._on_check_light_timeout, 10)

    ### for debug mode ###
    def __debug_stop_active_auto_mode_debug(self):
        print("end auto mode \n")
        Clock.unschedule(self.active_auto_mode_debug)

    ### for debug mode ###
    def __debug_on_active_auto_mode_debug(self):
        print("Start auto")
        Clock.schedule_interval(self.active_auto_mode_debug, 1)

    ### for debug mode ###
    def active_auto_mode_debug(self,dt):
        self.debug_counting += 1
        if self.debug_counting > 10:
            self.debug_stop_auto_mode = False
            self.debug_counting = 0
            status = ControlHelioStats.move_helio_out(self, ip=self.__light_checking_ip_operate)
            if status == False:
                print("fail to move light out off target!")
                self.ids.logging_process.text = "Fail to move light out off target!"
            else:
                print("Move heliostats out success.")
                self.ids.logging_process.text = "Move heliostats out success."
                self.list_pos_move_out.append({"id":self.path_data_heliostats[self.current_helio_index]['id'],"ip":self.path_data_heliostats[self.current_helio_index]['ip'],})
                self.__debug_stop_active_auto_mode_debug()
                Clock.schedule_once(self._increment_and_process, 0)
        else:
            ### process จำลองสมมุติระบบยังคำนวณหา diff อยู่
            self.ids.logging_process.text = "Operating heliostats..."
            print("counting => " + str(self.debug_counting))
            

    def _on_check_light_timeout(self, dt=None):
        print("30 seconds have passed, checking light result...")
        self.ids.logging_process.text = "30 seconds have passed, checking light result..."
        Clock.unschedule(self.checking_light_in_target)
        Clock.schedule_once(self._increment_and_process, 0)

    def _increment_and_process(self, dt=None):
        # Move index to next heliostat
        self.current_helio_index += 1
        self.process_next_helio()

    def _finish_auto_mode(self):
        print("Finish auto mode for all heliostats.")
        self.ids.logging_process.text = "Finish auto mode for all heliostats."
        self.status_finish_loop_mode_first = True
        self.helio_stats_fail_light_checking = ""
        self.__light_checking_ip_operate = ""
        self.pending_url = []
        self.standby_url = []
        self.fail_url = []
        self.list_fail_set_origin = []
        self.list_success_set_origin = []
        self.list_success_set_origin_store = []
        self.list_origin_standby = []
        self.list_pos_move_out = []
        self.path_data_heliostats = []
        self.path_data_not_found_list = []
        self.current_helio_index = 0
        self._on_check_light_timeout_event = None
        if not self.fail_checking_light:
            self.show_popup("Finish", "Finish auto mode for all heliostats.")
            

    def _handle_fail(self):
        # Show fail popup with ignore or try-again, etc.
        self.show_popup_with_ignore_con(
            title=self.fail_checking_light_desc['title'],
            message=self.fail_checking_light_desc['message'],
            h_data=self.helio_stats_fail_light_checking,
            action="try-again"
        )

    def __ignore_failure_checking_light_function(self, h_data ):
        self.list_success_set_origin.remove(h_data)
        self.handle_checking_light()

    def stanby_get_helio_stats_path(self):
        for h_data in self.list_success_set_origin:
            # print("stanby_get_helio_stats_path => ", h_data)
            list_path_data = CrudData.open_previous_data(self, self.camera_url_id.text, h_data['id'])
            if list_path_data['found'] == False:
                self.path_data_not_found_list.append(h_data['id'])
            else:
                self.path_data_heliostats.append({"path":list_path_data['data'],"id":h_data['id'],"ip":h_data['ip']})
        # print("stanby_get_helio_stats_path => ",self.path_data_heliostats)
    ### next checking 2 ###
    def handle_checking_light(self):
        print("Start handle_checking_light.")
        self.ids.logging_process.text = "Start handle_checking_light."
        self.list_success_set_origin_store = self.list_success_set_origin
        self.fail_checking_light_desc = {}
        self.fail_checking_light = False
        self.current_helio_index = 0
        self.stanby_get_helio_stats_path()
        # print("self.path_data_not_found_list => ", self.path_data_not_found_list)
        # print("self.path_data_heliostats => ", self.path_data_heliostats)
        if len(self.path_data_not_found_list) > 0:
            self.show_popup_continued(title="Warning", message="There are missing path or out of date \n"+ f"{self.path_data_not_found_list} \n if continue those heliostats will not operate." , action="to-process-next-helio")
        else:
            self.process_next_helio()

    ### next checking 1 ###
    def handler_set_origin(self, *args):
        print("Start set origin handler_set_origin...")
        self.ids.logging_process.text = "Start set origin handler_set_origin..."
        if self.operation_type_selection == "all":
            # try:
                print("Set origin to all heliostats mode.")
                for data in self.standby_url:
                    payload_x = ControlOrigin.send_set_origin_x(self,ip=data['ip'], id=data['id'])
                    if payload_x['is_fail'] == True:
                        self.list_fail_set_origin.append(payload_x)
                        self.ids.logging_process.text = "Warning found error connection" + str(data['ip'])

                    payload_y = ControlOrigin.send_set_origin_y(self,data['ip'], id=data['id'])
                    if payload_y['is_fail'] == True:
                        self.list_fail_set_origin.append(payload_y)
                        self.ids.logging_process.text = "Warning found error connection" + str(data['ip'])

                    if payload_x['is_fail'] == False and payload_y['is_fail'] == False:
                        self.list_success_set_origin.append(data)

                if len(self.list_fail_set_origin) > 0:
                    CrudData.save_fail_origin(self,self.list_fail_set_origin)
                    self.list_origin_standby= self.list_success_set_origin
                    self.show_popup_continued(title="warning", message="Number of origin fail " +f"{len(self.list_fail_set_origin)}", action="to-checking-light")
                else:
                    CrudData.save_origin(self,self.list_success_set_origin)
                    self.list_origin_standby= self.list_success_set_origin
                    print("finish set origin to all heliostats.\n")
                    self.ids.logging_process.text = "finish set origin to all heliostats."
                    self.handle_checking_light()
            # except Exception as e:
            #     print("error handler_set_origin func " + f"{e}")
            #     self.show_popup("Error",f"error in handler_set_origin function {e}")

        else:
            ip_helio_stats = CrudData.open_list_connection(self)
            for h_data in ip_helio_stats:
                if h_data['id'] == self.operation_type_selection:
                    
                    payload_x = ControlOrigin.send_set_origin_x(self,ip=h_data['ip'],id=h_data['id'])
                    if payload_x['is_fail'] == True:
                        self.list_fail_set_origin.append(payload_x)
                        self.ids.logging_process.text = "Warning found error connection" + str(data['ip'])
                    
                    payload_y = ControlOrigin.send_set_origin_y(self,ip=h_data['ip'],id=h_data['id'])
                    if payload_y['is_fail'] == True:
                        self.list_fail_set_origin.append(payload_y)
                        self.ids.logging_process.text = "Warning found error connection" + str(data['ip'])

                    if payload_x['is_fail'] == False and  payload_y['is_fail'] == False:
                        self.list_success_set_origin.append(h_data)
            
                    if len(self.list_fail_set_origin) > 0:
                        CrudData.save_fail_origin(self,payload=self.list_fail_set_origin)
                        self.list_origin_standby= self.list_success_set_origin
                        self.show_popup_continued(title="warning", message="Number of origin fail " +f"{len(self.list_fail_set_origin)}", action="to-checking-light")
                    else:
                        CrudData.save_origin(self,payload=self.list_success_set_origin)
                        self.list_origin_standby= self.list_success_set_origin
                        print("finish set origin to all heliostats.\n")
                        self.ids.logging_process.text = "finish set origin to all heliostats."
                        self.handle_checking_light() 
                        
                        # print("ok 2")

    ### finish checking ###
    def handler_loop_checking(self):
        # print("self.helio_stats_id.text => ", self.helio_stats_id.text.strip())
        print("Start checking connection heliostats.")
        self.ids.logging_process.text = "Start checking connection heliostats."
        if self.helio_stats_id.text.strip() == "all":
            self.operation_type_selection = self.helio_stats_id.text.strip()
            print("self.operation_type_selection => ", self.operation_type_selection)
            list_conn = CrudData.open_list_connection(self)
            # print("list_conn => ",list_conn)
            if len(list_conn) > 0:
                if self.is_loop_mode == True:
                    list_standby, list_pending, list_fail = ControlGetCurrentPOS.handler_get_current_pos(self,list_url=list_conn)
                    self.standby_url = list_standby
                    self.pending_url = list_pending
                    self.fail_url = list_fail
                    if len(self.fail_url) > 0:
                        self.show_popup_continued(title="Warning",  message=f"Number heliostats disconnected = {self.fail_url}", action="to-origin")
                    else:
                        print("Finish checking connection heliostats.\n")
                        self.ids.logging_process.text = "Finish checking connection heliostats."
                        self.handler_set_origin()
                else:
                    list_standby, list_pending, list_fail = ControlCheckConnHelioStats.handler_checking_connection(self,list_conn=list_conn)
                    self.standby_url = list_standby
                    self.pending_url = list_pending
                    self.fail_url = list_fail
                    if len(self.fail_url) > 0:
                        self.show_popup_continued(title="Warning",  message=f"Number heliostats disconnected = {len(self.fail_url)}", action="to-origin")
                    else:
                        print("Finish checking connection heliostats.\n")
                        self.ids.logging_process.text = "Finish checking connection heliostats."
                        self.handler_set_origin()
            else:
                print("Not found heliostats\n")
                self.ids.logging_process.text = "Not found heliostats"
                self.show_popup("Alert", "Not found any helio stats!")
        else:
            # print("ok 3")
            print("Finish checking connection heliostats.\n")
            self.ids.logging_process.text = "Finish checking connection heliostats."
            self.handler_set_origin()
    
    def active_auto_mode(self):
        h_id, _ = self.selection_url_by_id()
        if self.camera_endpoint != "" and self.helio_stats_id_endpoint != "":
            if self.status_auto.text == self.static_title_mode:
                if self.turn_on_auto_mode == False:
                    if int(self.number_center_light.text) == 1:
                        self.turn_on_auto_mode = True
                        self.helio_stats_selection_id = h_id
                        self.ids.label_auto_mode.text = "Auto on"
                        # self.update_loop_calulate_diff(1)
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
            ### move heliostats out ###
            status = ControlHelioStats.move_helio_out(self, ip=self.__light_checking_ip_operate)
            if status == False:
                print("Helio stats error move out!")
                self.show_popup_continued(title="Critical error move helio stats out", message="Cannot connection to helio stats when move out \nPlease check the connection and move heliostats out off target.", action="to-another-helio-stats")
            else:
                self.list_pos_move_out.append({"id":self.path_data_heliostats[self.current_helio_index]['id'],"ip":self.path_data_heliostats[self.current_helio_index]['ip'],})
                if len(self.list_success_set_origin) <= 0:
                    if self.is_loop_mode:
                        self.current_helio_index = 0
                        self.list_fail_set_origin = self.list_success_set_origin
                        Clock.schedule_once(self._increment_and_process, 0)
                    else:
                        self.turn_on_auto_mode = False
                        self.ids.label_auto_mode.text = "Auto off"
                        self.show_popup("Alert", "Camera is offline.")
                else:
                    Clock.schedule_once(self._increment_and_process, 0)

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
            self.ids.label_loop_mode.text = "Loop on"
        else:
            self.ids.label_loop_mode.text = "Loop off"
            self.is_loop_mode = False

    def list_fail_connection(self):
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        for url in self.fail_url:
            # print("list_fail_connection => ",url)
            grid = GridLayout(cols=2, size_hint=(1,1),height=40,spacing=10)
            label = Label(text=str(url), size_hint=(0.3,1))
            button_reconn = Button(text="Reconnect", size_hint=(0.2,1))
            button_reconn.bind(on_release=lambda instance: self.handler_reconn_helio(url=url) )
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

    def re_set_origin(self,payload):
        try:
            payload = {"topic":"origin","axis": payload['origin'],"speed": 400}
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
            button_origin_set.bind(on_release= lambda instance: self.re_set_origin(url=url))
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


