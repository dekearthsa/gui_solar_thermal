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
# from controller.control_get_current_pos import ControlGetCurrentPOS
# from controller.control_check_conn_heliostats import ControlCheckConnHelioStats
from controller.control_heliostats import ControlHelioStats
# from command.manual_command import ControllerManual
import time

class ControllerAuto(BoxLayout):
    def __init__(self,**kwargs ):
        
        super().__init__(**kwargs)
        self.is_loop_mode = False
        # self.helio_stats_id_endpoint = "" ### admin select helio stats endpoint
        self.helio_stats_selection_id = "" ####  admin select helio stats id
        self.helio_id = ""
        self.camera_endpoint = ""
        self.camera_selection = ""
        self.turn_on_auto_mode = False
        self.pending_url = []
        self.standby_url = []
        
        self.status_finish_loop_mode_first = False
        self.static_title_mode = "Auto menu || Camera status:On"
        self.time_loop_update = 2 ## 2 sec test update frame
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
        self.light_time_out_count = 1
        self.fail_checking_light_desc = {}
        self.fail_checking_light = False

        self.helio_stats_fail_light_checking = ""
        self.__light_checking_ip_operate = ""
        self.fail_url = [] # "192.168.0.1","192.168.0.2","192.168.0.2","192.168.0.2","192.168.0.2","192.168.0.2"
        self.list_fail_set_origin = [] # {"ip": "192.168.0.1", "origin": "x"},{"ip": "192.168.0.2", "origin": "x"}
        self.list_success_set_origin = []
        self.list_success_set_origin_store = []
        self.list_origin_standby = []
        # self.list_pos_move_out = []
        self.current_helio_index = 0
        self._on_check_light_timeout_event = None
        self.fail_to_tacking_light = False
        self.is_conn_fail_tacking_light = False

        self.path_data_heliostats = []
        self.path_data_not_found_list = []
        self.operation_type_selection = ""
        self.ignore_fail_connection_ip = False
        self.is_popup_show_fail_status = False
        self.is_move_helio_out_fail_status = False
        self.status_esp_send_timer = False
        self.status_esp_callback = False
        self.is_call_back_thread_on = False
        self.status_esp_origin_callback = False
        self.loop_timer_origin_callback = 1
        self.loop_timer_esp_callback = 1
        self.is_esp_move_fail = False
        self.current_pos_heliostats_for_moveout = {"topic":"mtt",}
        
        ### origin varibale ###
        self.loop_timeout_origin_is_finish = True
        self.origin_set_axis = "x"
        self.origin_axis_process = ""
        self.loop_delay_set_origin = 30 ## this func use handle_checking_origin_callback
        self.counting_set_origin = 0
        self.index_array_origin = 0
        self.range_of_heliostats = 0
        self.is_origin_set = False
        self.move_comp = 0
        self.ip_origin_process= ""
        self.delay_timeout_origin_xy = 50
        self.is_range_origin = False
        self.array_origin_range = []

        self.increment_move_out = 0
        # self.current_heliostats_data = []
        self.debug_counting = 0
        self.debug_counting_callback = 0

    def show_popup_continued(self, title, message ,action):

        if action != "tacking-fail":
            layout = BoxLayout(orientation='vertical', padding=10, spacing=30)
            label = Label(text=message)
            layout.add_widget(label)
            grid = GridLayout(cols=2, size_hint=(1,.3) ,height=30)
            popup = Popup(title=title,
                            content=layout,
                            auto_dismiss=False,
                            size_hint=(None, None), size=(1000, 600))

            if action == "to-origin":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="continue set origin")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()

            elif action == "to-auto":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="continue auto start")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()

            elif action == "to-checking-light":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="continue auto start")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()

            elif action == "try-again":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="try again")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()
            elif action == "to-process-next-helio":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="continue")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()
            elif action == "reconnect-auto-mode":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="Retry")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()
            elif action == "error-stop-heliostats":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="Retry")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()
            elif action == "reconnect-move-out":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="Retry")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()
            elif action == "f-origin":
                button_exit = Button(text="Exit")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="Continue")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()
            elif action == "redo-esp":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="Retry")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()
            elif action == "get-data-heliostats":
                button_exit = Button(text="Terminate")
                button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=True, is_light_checking=False))
                grid.add_widget(button_exit)
                button_con = Button(text="Retry")
                button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action, terminate=False, is_light_checking=False))
                grid.add_widget(button_con)
                layout.add_widget(grid)
                popup.open()

        elif action == "tacking-fail":
            layout = BoxLayout(orientation='vertical', padding=10, spacing=30)
            label = Label(text=message)
            layout.add_widget(label)
            grid = GridLayout(cols=3, size_hint=(1,.3) ,height=30)
            popup = Popup(title=title,
                            content=layout,
                            auto_dismiss=False,
                            size_hint=(None, None), size=(1000, 600))
            
            button_exit = Button(text="Terminate")
            button_exit.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process="Terminate", terminate=True, is_light_checking=True))
            grid.add_widget(button_exit)
            button_con = Button(text="Retry")
            button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process="Retry", terminate=False, is_light_checking=True))
            grid.add_widget(button_con)
            button_con = Button(text="Continue")
            button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process="Continue", terminate=False, is_light_checking=True))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup.open()

        # elif action == "reconnect-auto-mode-cal-diff":
        #     button_con = Button(text="Retry")
        #     button_con.bind(on_release=lambda instance: self.close_popup_and_continue(popup=popup, process=action))
        #     grid.add_widget(button_con)
        #     layout.add_widget(grid)
        #     popup.open()

    def close_popup_and_continue(self, popup, process, terminate, is_light_checking):
        popup.dismiss() 
        if is_light_checking == False:
            if process == "to-origin":
                if terminate:
                    self.force_off_auto()
                # else:
                #     self.handler_set_origin() # edit
            elif process == "to-checking-light":
                if terminate:
                    self.force_off_auto()
                else:
                    self.handle_checking_light()
            elif process == "to-auto":
                if terminate:
                    self.force_off_auto()
                # else:
                #     self.handler_set_origin()
            elif process == "try-again":
                if terminate:
                    self.force_off_auto()
                else:
                    self.handle_checking_light()
                
            elif process == "to-process-next-helio":
                if terminate:
                    self.force_off_auto()
                else:
                    self.process_next_helio()
            elif process == "reconnect-auto-mode":
                if terminate:
                    self.force_off_auto()
                else:
                    # self.__debug_on_active_auto_mode_debug()
                    self.__on_loop_auto_calculate_diff() ## for production mode

            elif process == "error-stop-heliostats": ## at light checking 
                if terminate:
                    self.force_off_auto()
                else:
                    self.light_time_out_count = 1
                    self.checking_light_in_target()
            elif process == "reconnect-move-out": ## 
                if terminate: 
                    self.force_off_auto()
                else:
                    self.__on_loop_auto_calculate_diff()
            elif process == "f-origin":
                if terminate: 
                    pass
                else:
                    print("sdsdsd")
                    self.force_set_origin()
            elif process == "redo-esp":
                if terminate:
                    self.force_off_auto()
                else:
                    self.is_esp_move_fail = False
            elif process == "get-data-heliostats":
                if terminate:
                    self.force_off_auto()
                else:
                    self.active_auto_mode()
        else:
            if process == "Terminate":
                self.force_off_auto()
            elif process == "Retry":
                self.fail_to_tacking_light = False
                self.current_helio_index -= 2
                Clock.schedule_once(self._increment_and_process, 0)
            elif process == "Continue":
                self.fail_to_tacking_light = False
                self.current_helio_index -= 1
                Clock.schedule_once(self._increment_and_process, 0)
    

    def show_popup_with_ignore_con(self, title, message, action):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text=message)
        layout.add_widget(label)
        grid = GridLayout(cols=2, size_hint=(1,.3) ,height=30)
        popup = Popup(title=title,
                        content=layout,
                        size_hint=(None, None), size=(1000, 600))
        if action == "rety-ignore":
            button_ignore = Button(text="Ignore and continue")
            button_ignore.bind(on_release=lambda instance: self.close_popup_continued_with_ignore_con(popup=popup,process=action))
            grid.add_widget(button_ignore)
            button_con = Button(text="try again")
            button_con.bind(on_release=lambda instance: self.close_popup_and_rety_connection_light_checking(popup=popup, process=action))
            grid.add_widget(button_con)
            layout.add_widget(grid)
            popup.open()

    def close_popup_and_rety_connection_light_checking(self, popup, process):
        popup.dismiss() 
        if process == "rety-ignore":
            try:
                status = requests.get("http://"+self.helio_stats_fail_light_checking['ip'])
                if status.status_code == 200:
                    # self.fail_checking_light_desc = {}
                    # self.helio_stats_fail_light_checking = ""
                    # self.handle_checking_light()
                    self._light_check_result = False
                    self.__light_checking_ip_operate = self.helio_stats_fail_light_checking['ip']
                    Clock.schedule_interval(self.checking_light_in_target, self.time_check_light_update)
                    self._on_check_light_timeout_event = Clock.schedule_once(self._on_check_light_timeout, 10)
                else:
                    self.show_popup_with_ignore_con(
                        title=self.fail_checking_light_desc['title'],
                        message=self.fail_checking_light_desc['message'],
                        action="rety-ignore"
                    )
            except Exception as e:
                self.show_popup_with_ignore_con(
                        title=self.fail_checking_light_desc['title'],
                        message=self.fail_checking_light_desc['message'],
                        action="rety-ignore"
                    )

    def close_popup_continued_with_ignore_con(self, popup, process):
        popup.dismiss() 
        if process == "rety-ignore":
            self.__ignore_failure_checking_light_function()

    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(1000, 600))
        popup.open()

    ### camera endpoint debug ###
    # def selection_url_by_id(self):
    #     try:
    #         with open('./data/setting/setting.json', 'r') as file:
    #             storage = json.load(file)
    #         self.__light_checking_ip_operate = storage['storage_endpoint']['helio_stats_ip']['ip']
    #         self.camera_endpoint = storage['storage_endpoint']['camera_ip']['ip']
    #         h_id =  storage['storage_endpoint']['helio_stats_ip']['id']
    #         c_id = storage['storage_endpoint']['camera_ip']['id']
    #         return h_id[1:], c_id
    #     except Exception as e:
    #         self.show_popup("Error", f"{e}")

    def checking_light_in_target(self,dt=None):
        print("start check light result " +  self.__light_checking_ip_operate + " light detect = " +self.number_center_light.text)
        self.ids.logging_process.text = "Start check light timeout " + f"{self.light_time_out_count}/30"
        self.light_time_out_count += 1
        ### production need to > 0 ###
        print("checking light")
        if int(self.number_center_light.text) == 1: ### for debug mode using 0 ### 
        # if int(self.number_center_light.text) > 0:
            status = ControlHelioStats.stop_move(self,ip=self.__light_checking_ip_operate)
            print("status ", status)
            if status:
                self._light_check_result = True
                self.__off_loop_checking_light()
                
            else:
                self.show_popup_continued(title="Error connection", message="Error connection while try to stop move heliostats " + f"{self.__light_checking_ip_operate}", action="error-stop-heliostats")
                # self.show_popup("Error connection", "Error connection ip" + f"{self.__light_checking_ip_operate}")

    def __off_loop_checking_light(self, dt=None):
        Clock.unschedule(self.checking_light_in_target)
        Clock.unschedule(self._on_check_light_timeout_event)
        ### change this to active_auto_mode for production ### 
        # self.__debug_on_active_auto_mode_debug()
        ### production ###
        self.active_auto_mode()

    def _on_check_light_timeout(self, dt=None):
        print("30 seconds have passed, checking light result...")
        self.ids.logging_process.text = "Fail to tacking " + f"{self.__light_checking_ip_operate}"
        self.fail_to_tacking_light = True 
        Clock.unschedule(self.checking_light_in_target)
        Clock.schedule_once(self._increment_and_process, 0)

    def process_next_helio(self, dt=None):
        # Check if we are done with all heliostats
        if self.fail_to_tacking_light == False:
            if self.status_finish_loop_mode_first == False:
                print("Loop using function use path.")
                self.ids.logging_process.text = "Loop using function use path."
                print("self.current_helio_index ",self.current_helio_index)
                print("self.path_data_heliostats ",self.path_data_heliostats)
                print("list_success_set_origin => ", self.list_success_set_origin)
                if self.ignore_fail_connection_ip == False:
                    if self.current_helio_index >= len(self.list_success_set_origin):
                            # All done
                        if self.is_loop_mode:
                            self.current_helio_index = 0
                            # self.list_fail_set_origin =self.list_success_set_origin
                        else:
                            self.force_off_auto()
                            return
                        
                self.ignore_fail_connection_ip = False
                h_data = self.path_data_heliostats[self.current_helio_index]
                self.helio_id = h_data['id']
                # 2. Send nearest time data
                result = ControlHelioStats.find_nearest_time_and_send(
                    self, list_path_data=h_data['path'], ip=h_data['ip']
                )
                if result['is_fail']:
                    # Fail to send => show error, store fail, break the entire process
                    self.fail_checking_light_desc = {
                        "title": "Error send path",
                        "message": "Fail to connect heliostats " + f"{h_data['ip']} \n if ignore this heliostats will not operate in loop!",
                    }

                    self.fail_checking_light = True
                    self.helio_stats_fail_light_checking = h_data
                    # print(self.helio_stats_fail_light_checking)
                    self.__handle_fail()
                    return
                # 3. Start checking the light
                print(f"Start auto mode. ip = {h_data['ip']}")
                self._light_check_result = False
                self.__light_checking_ip_operate = h_data['ip']
                # Schedule checking_light_in_target periodically
                Clock.schedule_interval(self.checking_light_in_target, self.time_check_light_update)
                # Schedule a timeout in 30 seconds to evaluate the result
                self._on_check_light_timeout_event = Clock.schedule_once(self._on_check_light_timeout, 30)
            else:
                print("loop using function move in heliostats.")
                self.ids.logging_process.text = "loop using function move in heliostats."
                print("self.current_helio_index ",self.current_helio_index)
                print("self.path_data_heliostats ",self.path_data_heliostats)
                if self.ignore_fail_connection_ip == False:
                    if self.current_helio_index >= len(self.list_success_set_origin):
                        # All done
                        if self.is_loop_mode:
                            self.current_helio_index = 0
                            # self.list_fail_set_origin = self.path_data_heliostats
                        else:
                            self._finish_auto_mode()
                            return
                self.ignore_fail_connection_ip = False
                h_data = self.path_data_heliostats[self.current_helio_index]

                # 2. Send nearest time data
                result = ControlHelioStats.move_helio_in(
                    self, ip=h_data['ip'],
                    target=self.camera_url_id.text,
                    heliostats_id=h_data['id']
                )
                self.helio_id = h_data['id']
                # print(result)

                if result['is_fail']:
                    # Fail to send => show error, store fail, break the entire process
                    self.fail_checking_light_desc = {
                        "title": "Error send path",
                        "message": "Fail to nearest path time to heliostats",
                    }
                    self.fail_checking_light = True
                    self.helio_stats_fail_light_checking = h_data
                    self.__handle_fail()
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
            self.show_popup_continued(title="Tacking fail", message="Fail to tacking ip " + f"{self.__light_checking_ip_operate}", action="tacking-fail")

    def _increment_and_process(self, dt=None):
        # Move index to next heliostat
        self.current_helio_index += 1
        self.process_next_helio()

    def _finish_auto_mode(self):
        print("Finish auto mode for all heliostats.")
        self.ids.logging_process.text = "Finish auto mode for all heliostats."
        self.status_finish_loop_mode_first = True
        self.is_origin_set = False
        self.helio_stats_fail_light_checking = ""
        self.__light_checking_ip_operate = ""
        self.pending_url = []
        self.standby_url = []
        self.fail_url = []
        self.list_fail_set_origin = []
        self.list_success_set_origin = []
        self.list_success_set_origin_store = []
        self.list_origin_standby = []
        # self.list_pos_move_out = []
        self.path_data_heliostats = []
        self.path_data_not_found_list = []
        self.current_helio_index = 0
        self._on_check_light_timeout_event = None
        if not self.fail_checking_light:
            self.show_popup("Finish", "Finish auto mode for all heliostats.")
            

    def __handle_fail(self):
        self.show_popup_with_ignore_con(
            title=self.fail_checking_light_desc['title'],
            message=self.fail_checking_light_desc['message'],
            action="rety-ignore"
        )

    def __ignore_failure_checking_light_function(self):
        self.path_data_heliostats.remove(self.helio_stats_fail_light_checking)
        self.list_success_set_origin = [item for item in self.list_success_set_origin if item['id'] != self.helio_stats_fail_light_checking['id']]
        if  self.current_helio_index >= len(self.path_data_heliostats):
            # self.current_helio_index = 0
            self.ignore_fail_connection_ip = True
            self.helio_stats_fail_light_checking = ""
            self.process_next_helio()
        else:
            # self.current_helio_index += 1
            self.ignore_fail_connection_ip = True
            self.helio_stats_fail_light_checking = ""
            self.process_next_helio()

    def stanby_get_helio_stats_path(self):
        for h_data in self.list_success_set_origin:
            print("stanby_get_helio_stats_path => ", h_data)
            list_path_data = CrudData.open_previous_data(self, self.camera_url_id.text, h_data['id'])
            if list_path_data['found'] == False:
                self.path_data_not_found_list.append(h_data['id'])
            else:
                self.path_data_heliostats.append({"path":list_path_data['data'],"id":h_data['id'],"ip":h_data['ip']})
        print("stanby_get_helio_stats_path => ",self.path_data_heliostats)

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
            print(self.path_data_heliostats)
            self.process_next_helio()

    ### function origin control ###
    def button_force_origin(self):
        if self.is_origin_set == False:
            self.show_popup_continued(title="Warning", message="Heliostats may fail to operate if their origin is not set.", action="f-origin")
        else:
            self.force_set_origin()
            self.show_popup(title="Alert", message="Off force heliostats.")

    def force_set_origin(self):
        if self.is_origin_set == True:
            self.ids.force_set_origin.text = "Force origin off"
            self.is_origin_set = False
        else:
            # print(self.helio_stats_id.text)
            storage = CrudData.open_list_connection(self)
            self.ids.force_set_origin.text = "Force origin on"
            self.is_origin_set = True
            if self.helio_stats_id.text == "all":
                self.list_success_set_origin = storage[1:]
                print("Save origin success")
            else:
                print()
                for h_data in storage:
                    if h_data['id'] == self.helio_stats_id.text:
                        self.standby_url = []
                        self.standby_url = [h_data]
                        self.list_success_set_origin = [h_data]
                        print("self.list_success_set_origin" , self.list_success_set_origin)
                        print("Save origin success")

    ### start origin ###
    def handler_set_origin(self, *args):
        print("Start set origin handler_set_origin...")
        self.ids.logging_process.text = "Start set origin handler_set_origin..."
        if self.is_range_origin == False:
            ip_helio_stats = CrudData.open_list_connection(self)
            # print("ip_helio_stats => ",ip_helio_stats)
            # print("self.operation_type_selection => ",self.helio_stats_id.text)
            if self.helio_stats_id.text == "all":
                self.range_of_heliostats = len(ip_helio_stats) - 1
                self.standby_url = ip_helio_stats[1:]
                self.list_success_set_origin = ip_helio_stats[1:]
                # print(self.standby_url)
                print("Set origin to all heliostats mode.")
                self.__on__counting_index_origin()
            else:
                for h_data in ip_helio_stats:
                    if h_data['id'] == self.helio_stats_id.text:
                        print("h_data['id']" , h_data['id'])
                        self.standby_url = []
                        self.standby_url = [h_data]
                        self.list_success_set_origin = [h_data]
                        self.range_of_heliostats = len(self.standby_url)
                        self.__on__counting_index_origin()
        else:
            self.range_of_heliostats = len(self.array_origin_range)
            self.list_success_set_origin = self.array_origin_range
            self.standby_url = self.array_origin_range


    def haddle_counting_index_origin(self,dt=None):
        # print("haddle_counting_index_origin start...")
        if self.loop_timeout_origin_is_finish == True:
            self.loop_timeout_origin_is_finish = False
            print("self.index_array_origin: " + str(self.index_array_origin) + " " + "self.range_of_heliostats: "+ str(self.range_of_heliostats))
            if self.index_array_origin == self.range_of_heliostats:
                print("Set origin finish")
                self.__off_counting_index_origin()
                self.origin_set_axis = None
            
            if self.origin_set_axis == 'x':
                print("haddle_counting_index_origin set origin X " + str(f"{self.standby_url[self.index_array_origin]['ip']}"))
                self.ip_origin_process = "x " + f"{self.standby_url[self.index_array_origin]['ip']}"
                payload_x = ControlOrigin.send_set_origin_x(
                    self,
                    ip=self.standby_url[self.index_array_origin]['ip'], 
                    id=self.standby_url[self.index_array_origin]['id']
                )
                
                if payload_x['is_fail'] == True:
                    self.list_fail_set_origin.append(payload_x)
                    self.ids.logging_process.text = "Warning found error connection" + str(self.standby_url[self.index_array_origin]['ip'])
                    self.index_array_origin += 1
                    self.loop_timeout_origin_is_finish = True
                    self.origin_set_axis = "x"
                else:
                    print("sleep x 50 sec")
                    time.sleep(self.delay_timeout_origin_xy) ## default = 50 sec
                    headers = {
                        'Content-Type': 'application/json'  
                    }
                    payload = {
                        "topic": "mtt",
                        "x": 300.0,
                        "y": 0.0
                    }
                    result =  requests.post("http://"+self.standby_url[self.index_array_origin]['ip']+"/update-data", data=json.dumps(payload), headers=headers, timeout=5)
                    print("sleep x 300 50 sec")
                    time.sleep(self.delay_timeout_origin_xy) ## default = 50 sec
                    if result.status_code == 200:
                        self.origin_axis_process = 'y' 
                        self.__on_thread_check_callback_origin()
                

            if self.origin_set_axis == 'y':
                print("haddle_counting_index_origin set origin Y " + str(f"{self.standby_url[self.index_array_origin]['ip']}"))
                self.ip_origin_process = "y " + f"{self.standby_url[self.index_array_origin]['ip']}"
                payload_y = ControlOrigin.send_set_origin_y(
                    self,
                    ip=self.standby_url[self.index_array_origin]['ip'], 
                    id=self.standby_url[self.index_array_origin]['id']
                )
                if payload_y['is_fail'] == True:
                    self.list_fail_set_origin.append(payload_y)
                    self.ids.logging_process.text = "Warning found error connection" + str(self.standby_url[self.index_array_origin]['ip'])
                    self.index_array_origin += 1
                    self.loop_timeout_origin_is_finish = True
                    self.origin_set_axis = "x"
                else:
                    print("sleep y 50 sec")
                    time.sleep(self.delay_timeout_origin_xy) ## default = 50 sec
                    headers = {
                        'Content-Type': 'application/json'  
                    }
                    payload = {
                        "topic": "mtt",
                        "x": 300.0,
                        "y": 300.0
                    }
                    result =  requests.post("http://"+self.standby_url[self.index_array_origin]['ip']+"/update-data", data=json.dumps(payload), headers=headers, timeout=5)
                    print("sleep y 300 50 sec")
                    time.sleep(self.delay_timeout_origin_xy) ## default = 50 sec
                    if result.status_code == 200:
                        self.origin_axis_process = 'y' 
                        self.__on_thread_check_callback_origin()
                        self.origin_axis_process = 'success' 
                        self.__on_thread_check_callback_origin()

            if self.origin_set_axis == 'success': 
                print("haddle_counting_index_origin set origin save.. "  + str(f"{self.standby_url[self.index_array_origin]['ip']} \n"))
                self.ip_origin_process = "save " + f"{self.standby_url[self.index_array_origin]['ip']}"
                self.list_success_set_origin.append(self.standby_url[self.index_array_origin])
                self.index_array_origin += 1
                self.origin_set_axis = "x"
                self.origin_axis_process = '' 
                self.loop_timeout_origin_is_finish = True

    def __off_counting_index_origin(self):
        Clock.unschedule(self.haddle_counting_index_origin) ## close thread 
        if len(self.list_fail_set_origin) > 0:
            CrudData.save_fail_origin(self,self.list_fail_set_origin)
            self.list_origin_standby= self.list_success_set_origin
            self.is_origin_set = True
            self.show_popup(title="warning", message="Number of origin fail " +f"{len(self.list_fail_set_origin)}")
            # self.show_popup(title="warning", message="Number of origin fail " +f"{len(self.list_fail_set_origin)}", action="to-checking-light")
        else:
            CrudData.save_origin(self,self.list_success_set_origin)
            self.list_origin_standby = self.list_success_set_origin
            print("finish set origin to all heliostats.\n")
            self.is_origin_set = True
            self.ids.logging_process.text = "finish set origin to all heliostats."
            # self.handle_checking_light()

    def __on__counting_index_origin(self):
        self.origin_set_axis = "x"
        Clock.schedule_interval(self.haddle_counting_index_origin, self.loop_timer_origin_callback) ## 2 sec

    def handle_checking_origin_callback(self,dt=None):
        ## if set origin it will delay 10 sec
        self.counting_set_origin += 1
        self.ids.logging_process.text = "Waiting set origin  " + self.ip_origin_process + " " + str(self.counting_set_origin) + "/" +"30"  ### default is 30 sec
        # print("Set origin wating callback from arduino.... " + str(self.counting_set_origin))
        if self.loop_delay_set_origin == self.counting_set_origin: ## loop_delay_set_origin is 10sec
            self.counting_set_origin = 0
            self.loop_timeout_origin_is_finish = True
            self.origin_set_axis = self.origin_axis_process
            self.__off_terminate_thread_origin()

    def __on_thread_check_callback_origin(self):
        Clock.schedule_interval(self.handle_checking_origin_callback, self.loop_timer_origin_callback) ## 2 sec

    def __off_terminate_thread_origin(self):
        self.ids.logging_process.text = "Finish set origin."
        Clock.unschedule(self.handle_checking_origin_callback)

    #### auto mode ####
    def control_auto_mode(self):
        if self.is_origin_set == True: 
            if self.ids.id_debug_mode.text == "debug off":
                self.ids.id_debug_mode.text = "debug on"
                self.ids.label_auto_mode.text = "Auto on"
                print("Start checking connection heliostats.")
                self.handle_checking_light()
            else:
                self.force_off_auto()
        else:
            self.show_popup(title="Alert", message="Origin must set first.")

    def force_off_auto(self):
        self.ids.id_debug_mode.text = "debug off"
        self.ids.label_auto_mode.text = "Auto off"
        self.is_origin_set = False
        self.is_esp_move_fail = False
        Clock.unschedule(self.checking_light_in_target)
        # Clock.unschedule(self.active_auto_mode_debug)
        Clock.unschedule(self.update_loop_calulate_diff)
        self.__off_loop_auto_calculate_diff()
        self._finish_auto_mode()

    def active_auto_mode(self):
        # h_id, _ = self.selection_url_by_id()
        # print("active_auto_mode => ",self.__light_checking_ip_operate)
        h_id = self.__light_checking_ip_operate
        try:
            data = requests.get("http://"+self.helio_get_data+"/",timeout=7)
            json_data =  data.json()
            self.current_pos_heliostats_for_moveout['x'] = json_data['currentX']
            self.current_pos_heliostats_for_moveout['y'] = json_data['currentY']
            ### Edit id  ####
            if self.camera_url_id.text != "" and self.__light_checking_ip_operate != "":
                print("if self.camera_url_id.text != "" and self.__light_checking_ip_operate != "":")
                if self.status_auto.text == self.static_title_mode:
                    print("if self.status_auto.text == self.static_title_mode:")
                    if self.turn_on_auto_mode == False:
                        print("self.turn_on_auto_mode == False:")
                        if int(self.number_center_light.text) == 1:
                            print("if int(self.number_center_light.text) == 1:")
                            self.turn_on_auto_mode = True
                            self.helio_stats_selection_id = h_id ###  <= must be id heliostats  ####
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
        except Exception as e:
            print("Connection error heliostats "+ f"{self.__light_checking_ip_operate}" + " in function active_auto_mode.")
            self.show_popup_continued(title="Connection error", message="Lost connection " +f"{self.__light_checking_ip_operate}", action="get-data-heliostats")
        
    
    ### checking status in when ESP32  ###
    def handler_checking_callback_esp(self, dt):
        if self.is_esp_move_fail == False:
            print("Wating arduino.... " + self.__light_checking_ip_operate + " " + str(self.debug_counting_callback))
            self.ids.logging_process.text = "Wating arduino.... " + self.__light_checking_ip_operate + " " + str(self.debug_counting_callback)
            self.debug_counting_callback += 1

            comp_status = requests.get("http://"+self.__light_checking_ip_operate)
            setJson = comp_status.json()
            print("setJson => ", setJson)
            # if setJson['move_comp'] == 0 and setJson['start_tracking'] == 1:
            if setJson['safety']['move_comp'] == 1 and setJson['safety']['start_trarcking'] == 0:
                self.status_esp_send_timer = False
                self.__off_checking_thread_callback()
            elif setJson['safety']['move_comp'] == 0 and setJson['safety']['start_trarcking'] == 0:
                self.is_esp_move_fail = True
                print("arduino dead check arduino! " + self.__light_checking_ip_operate)
                self.ids.logging_process.text = "Arduino status: Device is unhealthy!"
                self.show_popup_continued(title="Critical error", message="Arduino is unhealthy please check connection or device.", action="redo-esp")

    def __on_checking_thread_callback(self):
        if self.is_call_back_thread_on == False:
            self.is_call_back_thread_on = True
            self.debug_counting_callback = 0
            Clock.schedule_interval(self.handler_checking_callback_esp, self.loop_timer_esp_callback) ### set rety read 3 sec

    def __off_checking_thread_callback(self):
        
        try:
            with open("./data/setting/status_return.json", 'r') as file:
                storage = json.load(file)
                storage['esp_status_call_back'] = False
            with open("./data/setting/status_return.json", 'w') as file_change:
                json.dump(storage, file_change)
                self.is_call_back_thread_on = False
        except Exception as e:
            print("error save status in to status_return.json!")
        
        Clock.unschedule(self.handler_checking_callback_esp)
    ### ---end--- ###

    def update_loop_calulate_diff(self, dt):
        if self.is_call_back_thread_on == False:
            center_x, center_y, target_x, target_y = self.__extract_coordinates_pixel(self.center_frame_auto.text, self.center_target_auto.text)
            if self.status_auto.text == self.static_title_mode:
                now = datetime.now()
                timestamp = now.strftime("%d/%m/%y %H:%M:%S")
                path_time_stamp = now.strftime("%d_%m_%y")
                if abs(center_x - target_x) <= self.stop_move_helio_x_stats and abs(center_y - target_y) <= self.stop_move_helio_y_stats:
                    try:
                        payload = requests.get(url="http://"+self.__light_checking_ip_operate)
                        # print("payload => ", payload) 
                        setJson = payload.json()
                        self.__haddle_save_positon(
                                timestamp=timestamp,
                                pathTimestap=path_time_stamp,
                                helio_stats_id=self.helio_id,
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
                        self.__off_loop_auto_calculate_diff()
                        self.show_popup_continued(title="Error connection get calculate diff", message="Error connection "+f"{self.__light_checking_ip_operate}"+"\nplease check connection and click retry.", action="reconnect-auto-mode")
                else:
                    if self.status_esp_send_timer == False:
                        self.__send_payload(
                            axis=self.set_axis,
                            center_x=center_x,
                            center_y=center_y,
                            center_y_light=target_y,
                            center_x_light=target_x,
                            kp=self.set_kp,
                            ki=self.set_ki,
                            kd=self.set_kd,
                            max_speed=self.set_max_speed,
                            off_set=self.set_off_set,
                            status=self.set_status
                        )
                    else:
                        self.__on_checking_thread_callback()
            else:
                print("update_loop_calulate_diff else ")
                self.__off_loop_auto_calculate_diff()
                ### move heliostats out ###
                status = ControlHelioStats.move_helio_out(self, ip=self.__light_checking_ip_operate, payload=self.current_pos_heliostats_for_moveout)
                # time.sleep(10)
                if status == False:
                    print("Helio stats error move out!")
                    # self.__off_loop_auto_calculate_diff()
                    self.show_popup_continued(title="Critical error move helio stats out", message="Cannot connection to helio stats when move out \nPlease check the connection and move heliostats out off target.", action="reconnect-move-out")
                else:
                    print("loop on delay diff")
                    self.current_pos_heliostats_for_moveout = {"topic":"mtt",}
                    # self.list_pos_move_out.append({"id":self.path_data_heliostats[self.current_helio_index]['id'],"ip":self.path_data_heliostats[self.current_helio_index]['ip'],})
                    if len(self.list_success_set_origin) <= 0:
                        if self.is_loop_mode:
                            self.current_helio_index = 0
                            self.list_fail_set_origin = self.list_success_set_origin
                            self.__on_delay_move_out()
                        else:
                            self.turn_on_auto_mode = False
                            self.ids.label_auto_mode.text = "Auto off"
                    else:
                        self.__on_delay_move_out()


    def __on_loop_auto_calculate_diff(self):
        Clock.schedule_interval(self.update_loop_calulate_diff, self.time_loop_update)

    def __off_loop_auto_calculate_diff(self):
        self.status_esp_send_timer = False
        Clock.unschedule(self.update_loop_calulate_diff)

    def thread_delay_move_out(self,  dt=None):
        self.increment_move_out += 1
        if self.increment_move_out >= 10: ## delay 10 sec
            Clock.schedule_once(self._increment_and_process, 0)
            self.increment_move_out = 0
            self.__off_delay_move_out()

    def __on_delay_move_out(self):
        Clock.schedule_interval(self.thread_delay_move_out, 1)

    def __off_delay_move_out(self):

        Clock.unschedule(self.thread_delay_move_out)

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
                "move_comp": self.move_comp, ## move comp defaut = 0
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
            response = requests.post("http://"+self.__light_checking_ip_operate+"/auto-data", data=json.dumps(payload), headers=headers, timeout=5)
            print("=== DEBUG AUTO ===")
            print("End point => ","http://"+self.__light_checking_ip_operate+"/auto-data")
            print("payload => ",payload)
            print("reply status => ",response.status_code)
            print("\n")
            if response.status_code != 200:
                self.show_popup_continued(title="Error connection", message="Error connection "+f"{self.__light_checking_ip_operate}"+"\nplease check connection and click retry.", action="reconnect-auto-mode")
            else:
                self.status_esp_send_timer = True
                print("debug value post method = ",response)
        except Exception as e:
            self.show_popup_continued(title="Error connection", message="Error connection "+f"{self.__light_checking_ip_operate}"+"\nplease check connection and click retry.", action="reconnect-auto-mode")

    def __haddle_save_positon(self,timestamp,pathTimestap,helio_stats_id,camera_use,id,currentX, currentY,err_posx,err_posy,x,y,x1,y1,ls1,st_path,move_comp,elevation,azimuth):
        # print("helio_stats_id save => ", helio_stats_id)
        self.turn_on_auto_mode = False
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
        ControlHelioStats.move_helio_out(self, ip=self.__light_checking_ip_operate, payload=self.current_pos_heliostats_for_moveout)
        self.current_pos_heliostats_for_moveout = {"topic":"mtt",}
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
                    # self.show_popup("Finish", f"Auto mode off")
                    # self.turn_on_auto_mode = False
                    # self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    
                    self.__on_delay_move_out()
                else:
                    with open(path_file_by_date, mode='a', newline='', encoding='utf-8') as text_f:
                        text_f.write(perfixed_json+"\n")
                    # self.show_popup("Finish", f"Auto mode off")
                    # self.turn_on_auto_mode = False
                    # self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    self.__on_delay_move_out()
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
                    # self.show_popup("Finish", f"Auto mode off")
                    # self.turn_on_auto_mode = False
                    # self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    self.__on_delay_move_out()
                else:
                    with open(path_file_by_date, mode='a', newline='', encoding='utf-8') as text_f:
                        text_f.write(perfixed_json+"\n")
                    # self.show_popup("Finish", f"Auto mode off")
                    # self.turn_on_auto_mode = False
                    # self.ids.label_auto_mode.text = "Auto off"
                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    self.__on_delay_move_out()
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

    def haddle_clear_origin(self):
        self.is_range_origin = False
        self.array_origin_range = []
        self.status_finish_loop_mode_first = True
        self.is_origin_set = False
        self.helio_stats_fail_light_checking = ""
        self.__light_checking_ip_operate = ""
        self.pending_url = []
        self.standby_url = []
        self.fail_url = []
        self.list_fail_set_origin = []
        self.list_success_set_origin = []
        self.list_success_set_origin_store = []
        self.list_origin_standby = []
        self.path_data_heliostats = []
        self.path_data_not_found_list = []
        self.current_helio_index = 0
        self._on_check_light_timeout_event = None

    def haddle_add_origin(self):
        try:
            with open("./data/setting/connection.json", 'r') as file:
                connection_list = json.load(file)

            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            for url in connection_list['helio_stats_ip'][1:]:
                grid = GridLayout(cols=2, size_hint=(1,1), height=40, spacing=10)
                label = Label(text=str(url), size_hint=(0.3,1))
                button_origin_set = Button(text="Add", size_hint=(0.2,1))
                button_origin_set.bind(on_release= lambda instance: self.adding_origin(url=url))
                grid.add_widget(label)
                grid.add_widget(button_origin_set)
                layout.add_widget(grid)

            popup = Popup(
                title="Add heliostats to set origin",
                content=layout,
                size_hint=(None, None),
                size=(1050, 960),
                auto_dismiss=True
            )

            popup.open()

        except Exception as e:
            print("File not found!")

    def adding_origin(self, url):
        if len(self.array_origin_range) == 0:
            self.is_range_origin = True
            self.array_origin_range.append(url)
            self.show_popup(title="alert", message="Heliostats "+f"{url}"+ " is adding.")
        else:
            for i in self.array_origin_range:
                if i['ip'] == url['ip']:
                    self.show_popup(title="alert", message="Heliostats "+f"{url}"+ " is readly added.")
                    break 
                else:
                    self.array_origin_range.append(url)
                    self.show_popup(title="alert", message="Heliostats "+f"{url}"+ " is adding.")