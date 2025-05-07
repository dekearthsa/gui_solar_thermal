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
from controller.control_get_solar_cal import ControlCalSolar
from controller.control_heliostats import ControlHelioStats
import time
import logging 
from pysolar.solar import get_altitude, get_azimuth
from pysolar.radiation import get_radiation_direct
import mysql.connector
import pytz
logging.getLogger('urllib3').setLevel(logging.WARNING)
from camera_control.auto_screen_widget import SetAutoScreen

class ControllerAuto(BoxLayout):
    def __init__(self,**kwargs ):
        
        super().__init__(**kwargs)
        self.latitude = 14.382198  ### GEOLUXE lat 
        self.longitude = 100.842897 ### GEOLUXE lng
        self.time_zone = "Asia/Bangkok" ### Thailand time zone
        # = datetime.now(self.time_zone).astimezone(self.time_zone.utc)  # แปลงเป็น UTC
        self.is_loop_mode = False
        self.is_first_loop_finish = False
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
        self.time_loop_update = 1.5 ## default 1 sec test update frame แก้ตรงนี้นะครับปรับ loop เวลาคำนวณ diff auto mode
        self.time_check_light_update = 1
        self.stop_move_helio_x_stats = 4 ### Stop move axis x when diff in theshold
        self.stop_move_helio_y_stats = 4 ### Stop move axis y when diff in theshold
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
        self.move_out_delay_sec = 10 ## delay 10 sec default
        
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
        self.time_sleep_origin = 200
        self.is_range_origin = False
        self.array_origin_range = []
        self.speed_origin = 600 ## default speed 600
        self.move_out_pos_x = 100 
        self.move_out_pos_y = 100
        self.current_x_pos = 0
        self.current_y_pos = 0
        self.rety_origin = False

        ### database connection ###
        self.db_host= "localhost"
        self.db_user="root"
        self.db_password="rootpassword"
        self.db_database_name="solarthermal"
        self.db_port=3306

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
            elif action == "retry-origin":
                button_exit = Button(text="Exit")
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
            elif process == "retry-origin":
                if terminate:
                    pass 
                else:
                    self.rety_origin = True
                    self.haddle_set_index_origin()
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
                # print("self.current_helio_index ",self.current_helio_index)
                # print("self.path_data_heliostats ",self.path_data_heliostats)
                # print("list_success_set_origin => ", self.list_success_set_origin)
                if self.ignore_fail_connection_ip == False:
                    if self.current_helio_index >= len(self.list_success_set_origin):
                            # All done
                        if self.is_loop_mode:
                            # self.is_first_loop_finish = True
                            self.status_finish_loop_mode_first = True
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
                # print(f"Start auto mode. ip = {h_data['ip']}")
                self._light_check_result = False
                self.__light_checking_ip_operate = h_data['ip']
                # Schedule checking_light_in_target periodically
                Clock.schedule_interval(self.checking_light_in_target, self.time_check_light_update)
                # Schedule a timeout in 30 seconds to evaluate the result
                self._on_check_light_timeout_event = Clock.schedule_once(self._on_check_light_timeout, 30)
            else:
                print("loop using function move in heliostats.")
                self.ids.logging_process.text = "loop using function move in heliostats."
                # print("self.current_helio_index ",self.current_helio_index)
                # print("self.path_data_heliostats ",self.path_data_heliostats)
                if self.ignore_fail_connection_ip == False:
                    if self.current_helio_index >= len(self.list_success_set_origin):
                        # All done
                        if self.is_loop_mode:
                            # self.is_first_loop_finish = True
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
                # print('move in result: ', result)
                self.helio_id = h_data['id']
                # print(result)

                if result['is_fail']:
                    # Fail to send => show error, store fail, break the entire process
                    self.fail_checking_light_desc = {
                        "title": "Error send path",
                        "message": "Fail to find path",
                    }
                    self.fail_checking_light = True
                    self.helio_stats_fail_light_checking = h_data
                    self.__handle_fail()
                    return
                
                result_ner = ControlHelioStats.find_nearest_time_and_send(
                    self, list_path_data=result['path'], ip=h_data['ip']
                )
                # print("result_ner => ", result_ner)
                if result_ner['is_fail']:
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
                # print(f"Start auto mode. ip = {h_data['ip']}")
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
            # print("stanby_get_helio_stats_path => ", h_data)
            list_path_data = CrudData.open_previous_data(self, target=self.camera_url_id.text,heliostats_id=h_data['id'])
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
        if self.status_finish_loop_mode_first == True:
            self.process_next_helio()
        else:
            if len(self.path_data_not_found_list) > 0:
                self.show_popup_continued(title="Warning", message="There are missing path or out of date \n"+ f"{self.path_data_not_found_list} \n if continue those heliostats will not operate." , action="to-process-next-helio")
            else:
                # print(self.path_data_heliostats)
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
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            self.speed_origin = setting_data['control_speed_distance']['auto_mode']['speed']
            self.time_sleep_origin = setting_data['control_speed_distance']['auto_mode']['time_sleep_origin']
            self.ids.logging_process.text = "Start set origin handler_set_origin..."
            if self.is_range_origin == False:
                ip_helio_stats = CrudData.open_list_connection(self)
                if self.helio_stats_id.text == "all":
                    self.range_of_heliostats = len(ip_helio_stats) - 1
                    self.standby_url = ip_helio_stats[1:]
                    self.list_success_set_origin = ip_helio_stats[1:]
                    # print(self.standby_url)
                    print("Set origin to all heliostats mode.")
                    # self.__on__counting_index_origin() ### Old set origin version
                    self.haddle_set_index_origin()
                else:
                    for h_data in ip_helio_stats:
                        if h_data['id'] == self.helio_stats_id.text:
                            print("h_data['id']" , h_data['id'])
                            self.standby_url = []
                            self.standby_url = [h_data]
                            self.list_success_set_origin = [h_data]
                            self.range_of_heliostats = len(self.standby_url)
                            # self.__on__counting_index_origin()  ### Old set origin version
                            self.haddle_set_index_origin()
            else:
                self.range_of_heliostats = len(self.array_origin_range)
                self.list_success_set_origin = self.array_origin_range
                self.standby_url = self.array_origin_range
        except Exception as e:
            print("Error handler_set_origin =>  ", e)
        
    def haddle_set_index_origin(self):
        print("haddle_set_index_origin start...")
        list_origin_raw = []
        list_set_origin_step1 = []
        list_set_origin_step2 = []
        list_set_origin_step3 = []
        list_final_origin = []

        if self.rety_origin == False:
            list_origin_raw = self.standby_url
        else:
            list_origin_raw = self.list_fail_set_origin
    
        print("Set origin X")
        for h_data in list_origin_raw:
            payload_x = ControlOrigin.send_set_origin_x(
                        self,
                        ip=h_data['ip'], 
                        id=h_data['id']
                    )
            if payload_x['is_fail'] == True:
                self.list_fail_set_origin.append(h_data)
                self.ids.logging_process.text = "Warning found error connection" + h_data['ip']
            else:
                list_set_origin_step1.append(h_data)

        print("Set timeout origin X")
        time.sleep(self.time_sleep_origin)

        headers = {'Content-Type': 'application/json'  }
        payload = {"topic": "mtt","speed": self.speed_origin,"x": 300.0,"y": 0.0}
        for h_data in list_set_origin_step1:
            try:
                result =  requests.post("http://"+h_data['ip']+"/update-data", data=json.dumps(payload), headers=headers, timeout=5)
                if result.status_code != 200:
                    self.list_fail_set_origin.append(h_data)
                else:
                    list_set_origin_step2.append(h_data)
            except Exception as e:
                print("Error haddle_set_index_origin = ",e)
                self.list_fail_set_origin.append(h_data)
        print("Set timeout origin X 300")
        time.sleep(self.time_sleep_origin)

        for h_data in list_set_origin_step2:
            payload_y = ControlOrigin.send_set_origin_y(
                self,
                ip=h_data['ip'], 
                id=h_data['id']
            )
            if payload_y['is_fail'] == True:
                self.list_fail_set_origin.append(h_data)
                self.ids.logging_process.text = "Warning found error connection" + h_data['ip']
            else:
                list_set_origin_step3.append(h_data)
        print("Set timeout origin Y")
        time.sleep(self.time_sleep_origin)

        headers = {'Content-Type': 'application/json'  }
        payload = {"topic": "mtt","speed": self.speed_origin,"x": 300.0,"y": 300.0}
        for h_data in list_set_origin_step3:
            try:
                result =  requests.post("http://"+h_data['ip']+"/update-data", data=json.dumps(payload), headers=headers, timeout=5)
                if result.status_code != 200:
                    self.list_fail_set_origin.append(h_data)
                else:
                    list_final_origin.append(h_data)
            except Exception as e:
                print("Error haddle_set_index_origin = ",e)
                self.list_fail_set_origin.append(h_data)
        print("Set timeout origin X 300")
        time.sleep(self.time_sleep_origin)

        if len(self.list_fail_set_origin) == 0:
            self.rety_origin = False
            self.origin_set_axis = None
            self.list_success_set_origin = list_final_origin
            self.is_origin_set = True
            self.ids.logging_process.text = "finish set origin to all heliostats."
            self.show_popup(title="Alert", message="Finish set origin.")
            print("Set origin finish")
        else:
            self.rety_origin = False
            self.is_origin_set = True
            self.ids.logging_process.text = "Some of heliostats are fail to set origin"
            self.show_popup_continued(title="warning", message="Finish origin but some origin fail \n" +f"{self.list_fail_set_origin}",action="retry-origin")


    #### auto mode ####
    def control_auto_mode(self):
        if self.is_origin_set == True: 
            if self.ids.label_auto_mode.text == "Auto off":
                self.ids.label_auto_mode.text = "Auto on"
                print("Start checking connection heliostats.")
                self.handle_checking_light()
            else:
                self.force_off_auto()
        else:
            self.show_popup(title="Alert", message="Origin must set first.")

    def force_off_auto(self):
        self.is_first_loop_finish = False
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
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            self.move_out_pos_x = setting_data['control_speed_distance']['auto_mode']['moveout_x_stay']
            self.move_out_pos_y = setting_data['control_speed_distance']['auto_mode']['moveout_y_stay']
            self.move_out_delay_sec = setting_data['control_speed_distance']['auto_mode']['moveout_delay_sec']
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
                            self.helio_stats_selection_id = self.__light_checking_ip_operate ###  <= must be id heliostats  ####
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
            self.show_popup(title="Connection error", message="Cannot open file ./data/setting/setting.json\n setting.json is missing.")
        
    
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
                        payload = requests.get(url="http://"+self.__light_checking_ip_operate, timeout=30)
                        setJson = payload.json()
                        # print("Start Save pos...")
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
                        print("error update_loop_calulate_diff => ", e)
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
                try:
                    payload = requests.get(url="http://"+self.__light_checking_ip_operate)
                    setJson = payload.json()
                    with open('./data/setting/setting.json', 'r') as file:
                        setting_data = json.load(file)
                    self.current_pos_heliostats_for_moveout['x'] = setJson['currentX'] -  setting_data['control_speed_distance']['auto_mode']['moveout_x_stay']
                    self.current_pos_heliostats_for_moveout['y'] = setJson['currentY'] +  setting_data['control_speed_distance']['auto_mode']['moveout_y_stay']
                    self.current_pos_heliostats_for_moveout['speed'] = setting_data['control_speed_distance']['auto_mode']['speed']
                    status = ControlHelioStats.move_helio_out(self, ip=self.__light_checking_ip_operate, payload=self.current_pos_heliostats_for_moveout)
                    if status == False:
                        print("Helio stats error move out!")
                        self.show_popup_continued(title="Critical error move helio stats out", message="Cannot connection to helio stats when move out \nPlease check the connection and move heliostats out off target.", action="reconnect-move-out")
                    else:
                        print("loop on delay diff")
                        self.current_pos_heliostats_for_moveout = {"topic":"mtt",}
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
                except Exception as e:
                    print("Helio stats error move out connection")
                    self.show_popup_continued(title="Connection error", message="Connection error "+ f"{self.__light_checking_ip_operate}", action="reconnect-move-out")


    def __on_loop_auto_calculate_diff(self):
        Clock.schedule_interval(self.update_loop_calulate_diff, self.time_loop_update)

    def __off_loop_auto_calculate_diff(self):
        self.status_esp_send_timer = False
        Clock.unschedule(self.update_loop_calulate_diff)

    def thread_delay_move_out(self,  dt=None):
        self.increment_move_out += 1
        if self.increment_move_out >= self.move_out_delay_sec: ## delay 10 sec default
            Clock.schedule_once(self._increment_and_process, 0)
            self.increment_move_out = 0
            self.__off_delay_move_out()

    def __on_delay_move_out(self):
        # print("finish-- \n")
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
            # print("End point => ","http://"+self.__light_checking_ip_operate+"/auto-data")
            print("payload => ",payload)
            # print("reply status => ",response.status_code)
            self.status_esp_send_timer = True
            # print("debug value post method = ",response)
        except Exception as e:
            print("error send pyload diff", e)
            self.show_popup_continued(title="Error connection", message="Error connection "+f"{self.__light_checking_ip_operate}"+"\nplease check connection and click retry.", action="reconnect-auto-mode")
    def button_debug_insertDB(self):
        # error_x, error_y = SetAutoScreen.get_error_x_y(self)
        now = datetime.now()
        data_in = {
            "heliostats_id": "test",
            "timestamp": str(now),
            "string_date":str(now.strftime("%d/%m/%y %H:%M:%S")),
            "is_day": 1,
            "is_month": 1,
            "is_year": 1,
            "is_lat": 15.01,
            "is_lng": 15.01,
            "camera": "top",
            "altitude": 12.333,
            "azimuth": 12.333,
            "azimuth_gyro": 13.444,
            "elevation_gyro": 123.222,
            "declination": 13.443,
            "hour_angle": 33.443,
            "radiation": 31.232,
            "x": 13.44,
            "y": 12.32,
            "error_x": 12.33,
            "error_y": 12.33
        }
        self.insert_into_db(data_in=data_in)

    def insert_into_db(self, data_in):
        try:
            ### STORE ERROR X Y ###
            error_x, error_y = SetAutoScreen.get_error_x_y(self)
            
            conn = mysql.connector.connect(
                host=self.db_host,
                user=self.db_user,
                password=self.db_password,
                database=self.db_database_name,
                port=self.db_port
            )
            cursor = conn.cursor()
            query = """INSERT INTO solar_data (heliostats_id, timestamp_s, string_date,is_day, is_month, is_year,is_lat ,is_lng ,camera, altitude, azimuth,azimuth_gyro, elevation_gyro, declination, hour_angle, radiation, x, y, error_x, error_y) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
            # query = """INSERT INTO solar_data (heliostats_id, timestamp_s, string_date,is_day, is_month, is_year,is_lat ,is_lng ,camera, altitude, azimuth,azimuth_gyro, elevation_gyro, declination, hour_angle, radiation, x, y) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
            values = (
                data_in['heliostats_id'],
                data_in['timestamp'],
                data_in['string_date'],
                data_in['is_day'],
                data_in['is_month'],
                data_in['is_year'],
                data_in['is_lat'],
                data_in['is_lng'],
                data_in['camera'],
                data_in['altitude'],
                data_in['azimuth'],
                data_in['azimuth_gyro'],
                data_in['elevation_gyro'],
                data_in['declination'],
                data_in['hour_angle'],
                data_in['radiation'],
                data_in['x'],
                data_in['y'],
                float(error_x),
                float(error_y)
                )
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
        except Exception as e:
            print("Insert database error" + f"{e}")

    def __haddle_save_positon(self,timestamp,pathTimestap,helio_stats_id,camera_use,id,currentX, currentY,err_posx,err_posy,x,y,x1,y1,ls1,st_path,move_comp,elevation,azimuth):
        print("helio_stats_id save => ", helio_stats_id)
        self.turn_on_auto_mode = False
        with open('./data/setting/setting.json', 'r') as file:
            storage = json.load(file)

        now = datetime.now()
        path_time_stamp = now.strftime("%d_%m_%y"+"_"+helio_stats_id)
        is_day = now.strftime("%d")
        is_month = now.strftime("%m")
        is_year = now.strftime("%y")
        timing =  now.strftime("%H:%M:%S")
        adding_path_data = {
            "timestamp": timing,
            "x":  currentX,
            "y": currentY,
        }
        #### Edit
        adding_path_data_gyro = {
            "timestamp": timing,
            "elevation":  elevation,
            "azimuth": azimuth,
        }

        tz = pytz.timezone(self.time_zone)
        time = datetime.now(tz)  # Get current local time
        is_time = time.astimezone(pytz.utc)  # Convert to UTC
        is_altitude = get_altitude(self.latitude, self.longitude,is_time)
        is_azimuth = get_azimuth(self.latitude, self.longitude,is_time)
        declination = ControlCalSolar.get_solar_declination(self,now)  # มุมเอนเอียงของดวงอาทิตย์
        hour_angle = ControlCalSolar.get_solar_hour_angle(self,now, self.longitude)  # มุมชั่วโมงของดวงอาทิตย์
        radiation = get_radiation_direct(is_time, self.latitude)  # การแผ่รังสีแสงอาทิตย์
        adding_in_database = {
            "heliostats_id":str(helio_stats_id),
            "timestamp": str(now),
            "string_date":str(now.strftime("%d/%m/%y %H:%M:%S")),
            "is_day": int(is_day),
            "is_month": int(is_month),
            "is_year": int(is_year),
            "is_lat": round(float(self.latitude),6),
            "is_lng": round(float(self.longitude), 6),
            "altitude": round(float(is_altitude),6),
            "azimuth": round(float(is_azimuth),6),
            "azimuth_gyro": round(float(azimuth),6),
            "elevation_gyro": round(float(elevation),6),
            "declination":round(float(declination),6),
            "hour_angle": round(float(hour_angle),6),
            "radiation": round(float(radiation),6),
            "x": float(currentX),
            "y": float(currentY),
        }
        
        json_str = json.dumps(adding_path_data)
        json_str_gyro = json.dumps(adding_path_data_gyro)
        perfixed_json = f"*{json_str}"
        perfixed_gyro_json = f"*{json_str_gyro}"
        self.current_pos_heliostats_for_moveout['x'] = currentX -  storage['control_speed_distance']['auto_mode']['moveout_x_stay']
        self.current_pos_heliostats_for_moveout['y'] = currentY +  storage['control_speed_distance']['auto_mode']['moveout_y_stay']
        self.current_pos_heliostats_for_moveout['speed'] = storage['control_speed_distance']['auto_mode']['speed']
        # print("Try to move-out")
        ControlHelioStats.move_helio_out(self, ip=self.__light_checking_ip_operate, payload=self.current_pos_heliostats_for_moveout)
        # print("Move out success.")
        self.current_pos_heliostats_for_moveout = {"topic":"mtt",}
        ### insert into db ###
        
        ### end insert into db ###
        if storage['storage_endpoint']['camera_ip']['id'] == "camera-bottom":
            adding_in_database['camera'] = "bottom"
            # print("Try to save in db")
            self.insert_into_db(data_in=adding_in_database)
            # print("Success save in db")
            # filename = "./data/calibrate/result/error_data.csv"
            path_file_by_date = f"./data/calibrate/result/{path_time_stamp}/data.txt"
            path_folder_by_date = f"./data/calibrate/result/{path_time_stamp}" 
            path_file_by_date_gyro = f"./data/calibrate_gyro/{path_time_stamp}.txt" #### Edit
            # path_folder_by_date_gryo = f"./data/calibrate_gyro/{path_time_stamp}"
            # path_folder_by_date_gyro = f"./data/calibrate_gyro/{path_time_stamp}.txt"  #### Edit
            # filepath = os.path.join(os.getcwd(), filename)
            filepath_by_date = os.path.join(os.getcwd(), path_folder_by_date)
            check_file_path = os.path.isdir(filepath_by_date) 

            # filepath_by_date_gyro = os.path.join(os.getcwd(), path_folder_by_date_gryo) #### Edit
            # check_file_path_gyro = os.path.isdir(filepath_by_date_gyro) #### Edit
            # try:
            if check_file_path == False:
                    os.mkdir(path_folder_by_date)
                    with open(path_file_by_date, mode='w', newline='') as text_f:
                        text_f.write(perfixed_json+"\n")
                    with open(path_file_by_date_gyro, mode='a', newline='') as text_f:
                        text_f.write(perfixed_gyro_json+"\n")
                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    
                    self.__on_delay_move_out()
            else:
                    with open(path_file_by_date, mode='a', newline='', encoding='utf-8') as text_f:
                        text_f.write(perfixed_json+"\n")
                    with open(path_file_by_date_gyro, mode='a', newline='') as text_f:
                        text_f.write(perfixed_gyro_json+"\n")
                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    self.__on_delay_move_out()

            # except Exception as e:
            #     self.turn_on_auto_mode = False
            #     self.ids.label_auto_mode.text = "Auto off"
            #     self.__off_loop_auto_calculate_diff()
            #     self.show_popup("Error",f"Error saving file:\n{str(e)}")  

        else:
            adding_in_database['camera'] = "top"
            self.insert_into_db(data_in=adding_in_database)
            path_file_by_date = f"./data/receiver/result/{path_time_stamp}/data.txt"
            path_folder_by_date = f"./data/receiver/result/{path_time_stamp}"
            path_file_by_date_gyro = f"./data/receiver_gyro/{path_time_stamp}.txt" #### Edit
            filepath_by_date = os.path.join(os.getcwd(), path_folder_by_date)
            check_file_path = os.path.isdir(filepath_by_date)
            # try:
            if check_file_path == False:
                    os.mkdir(path_folder_by_date)
                    with open(path_file_by_date, mode='w', newline='') as text_f:
                        text_f.write(perfixed_json+"\n")
                    with open(path_file_by_date_gyro, mode='a', newline='') as text_f:
                        text_f.write(perfixed_gyro_json+"\n")
                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    self.__on_delay_move_out()
            else:
                    with open(path_file_by_date, mode='a', newline='', encoding='utf-8') as text_f:
                        text_f.write(perfixed_json+"\n")
                    with open(path_file_by_date_gyro, mode='a', newline='') as text_f:
                        text_f.write(perfixed_gyro_json+"\n")

                    self.__off_loop_auto_calculate_diff()
                    print("move heliostats out...")
                    self.ids.logging_process.text = "move heliostats out"
                    self.__on_delay_move_out()

            # except Exception as e:
            #     self.turn_on_auto_mode = False
            #     self.ids.label_auto_mode.text = "Auto off"
            #     self.__off_loop_auto_calculate_diff()
            #     self.show_popup("Error",f"Error saving file:\n{str(e)}") 

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

    def active_datenow(self):
        if self.status_finish_loop_mode_first == True:
            self.status_finish_loop_mode_first = False
            self.show_popup(title="Update", message="Focus off current date")
        else:
            self.status_finish_loop_mode_first = True
            self.show_popup(title="Update", message="Focus on current date")
    
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
                button_origin_set.bind(on_release= lambda instance, url=url:self.adding_origin(url=url))
                # print(url)
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
        print(url)
        print(self.array_origin_range)
        if len(self.array_origin_range) == 0:
            self.is_range_origin = True
            self.array_origin_range.append(url)
            self.show_popup(title="alert", message="Heliostats "+f"{url}"+ " is adding.")
        else:
            for i in self.array_origin_range:
                if i['ip'] == url['ip']:
                    self.show_popup(title="alert", message="Heliostats "+f"{i}"+ " is readly added.")
                    break 
                else:
                    self.array_origin_range.append(url)
                    self.show_popup(title="alert", message="Heliostats "+f"{i}"+ " is adding.")
                    
                    
    def handler_set_mtt(self, url):
            try:
                with open('./data/setting/connection.json', 'r') as file:
                        connection_list = json.load(file)
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file) 
                
                payload = {
                    "topic": "mtt",
                    "speed": setting_data['control_speed_distance']['auto_mode']['speed'],
                    "x":300.0,
                    "y": 300.0
                }
                print("payload => ",url)
                if url == "all":
                    for h_data in connection_list['helio_stats_ip'][1:]:
                        response = requests.post("http://"+h_data['ip']+"/update-data", json=payload, timeout=5)
                        print("all => ",response.status_code)
                        if response.status_code != 200:
                            self.show_popup("Error connection", f"Requests status code {str(response.status_code)}")
                else:
                    response = requests.post("http://"+url+"/update-data", json=payload, timeout=5)
                    print(f"url: {url} => ",response.status_code)
                    if response.status_code != 200:
                        self.show_popup("Error connection", f"Requests status code {str(response.status_code)}")
            except Exception as e:
                print("handler_set_mtt error " + f"{e}") 
                self.show_popup("Error connection", f"Erorr at {str(e)}")


    def show_popup_mtt(self):
        try:
            with open('./data/setting/connection.json', 'r') as file:
                connection_list = json.load(file)

            layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
            for h_data in connection_list['helio_stats_ip']:
                grid = GridLayout(cols=2, size_hint=(1,1), height=40, spacing=10)
                label = Label(text=str(h_data), size_hint=(0.3,1))
                button_mtt_set = Button(text="Send MTT", size_hint=(0.2,1))
                button_mtt_set.bind(on_release= lambda instance, url_d=h_data['ip']:self.handler_set_mtt(url=url_d))
                grid.add_widget(label)
                grid.add_widget(button_mtt_set)
                layout.add_widget(grid)
            popup = Popup(
                title="Send MTT",
                content=layout,
                size_hint=(None, None),
                size=(1050, 960),
                auto_dismiss=True
            )
            popup.open()
        except Exception as e:
            print("error show_popup_mtt "+f"{e}")
            # print("error show_popup_mtt "+ f"{e}")

    def show_popup_force_off_auto_warning(self):
        message = "Warning, are you sure to off auto mode?"
        title = "Warning"
        layout = BoxLayout(orientation='vertical', padding=10, spacing=30)
        label = Label(text=message)
        layout.add_widget(label)
        grid = GridLayout(cols=2, size_hint=(1,.3) ,height=30)
        popup = Popup(title=title,
                            content=layout,
                            auto_dismiss=False,
                            size_hint=(None, None), size=(1000, 600))
            
        button_con = Button(text="Exit")
        button_con.bind(on_release=lambda instance: self.close_popup_force_off(popup=popup, process="Exit"))
        grid.add_widget(button_con)
        button_con = Button(text="Force off auto")
        button_con.bind(on_release=lambda instance: self.close_popup_force_off(popup=popup, process="Continue"))
        grid.add_widget(button_con)
        layout.add_widget(grid)
        popup.open()
    
    def close_popup_force_off(self,popup, process):
        popup.dismiss() 
        if process == "Continue":
            self.force_off_auto()

    def handler_force_off_btn(self):
        try:
            self.ids.logging_process = "Stopping heliostats..."
            response = requests.post("http://"+self.__light_checking_ip_operate+"/update-data", json={"topic":"stop"}, timeout=30)
            if response.status_code != 200:
                self.ids.logging_process = "Connection error POST " + f"{self.__light_checking_ip_operate}"
                print("handler_force_off_btn => error equests.post"+ f"{response.status_code}")
                self.show_popup(title="Connection error", message="func handler_force_off_btn command stop"+ f"{response.status_code}")
            self.ids.logging_process = "Heliostats is stop."
            time.sleep(1)

            self.ids.logging_process = "Try to get current POS..."
            payload = requests.get(url="http://"+self.  __light_checking_ip_operate, timeout=30)
            if payload.status_code != 200:
                self.ids.logging_process = "Connection error GET " + f"{self.__light_checking_ip_operate}"
                print("handler_force_off_btn => error requests.get"+ f"{payload.status_code}")
                self.show_popup(title="Connection error", message="func handler_force_off_btn command get current pos "+ f"{payload.status_code}")
            setJson = payload.json()
            self.ids.logging_process = "Success GET cu"
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            ### Notic หลักการทำงาสน
            self.current_pos_heliostats_for_moveout['x'] = setJson['currentX'] - setting_data['control_speed_distance']['auto_mode']['moveout_x_stay']
            self.current_pos_heliostats_for_moveout['y'] =  setJson['currentY'] +  setting_data['control_speed_distance']['auto_mode']['moveout_y_stay']
            self.current_pos_heliostats_for_moveout['speed'] = setting_data['control_speed_distance']['auto_mode']['speed']
            status = ControlHelioStats.move_helio_out(self, ip=self.__light_checking_ip_operate, payload=self.current_pos_heliostats_for_moveout)
            if status['is_fail']:
                print("handler_force_off_btn => error move_helio_out"+ f"{response.status_code}")
                self.show_popup(title="Connection error", message="func handler_force_off_btn command move_helio_out"+ f"{response.status_code}")
            time.sleep(2)
            self.force_off_auto()
        except Exception as e:
            self.ids.logging_process = "Connection error " + f"{self.__light_checking_ip_operate}"
            print("handler_force_off_btn error" + f"{e}")
            self.show_popup(title="Connection error", message="func handler_force_off_btn connection error \n"+ f"{e}" + "\n please try agian.") 

    ## Notic 
    def move_all_by_using_path(self):
        if len(self.list_success_set_origin) <= 0 :
            self.show_popup(title="Alert", message="set origin to heliostats first.")
        else:
            if len(self.path_data_heliostats) <= 0:
                for h_data in self.list_success_set_origin:
                    list_path_data = CrudData.open_previous_data(self, target=self.camera_url_id.text,heliostats_id=h_data['id'])
                    if list_path_data['found'] == False:
                        self.path_data_not_found_list.append(h_data['id'])
                    else:
                        self.path_data_heliostats.append({"path":list_path_data['data'],"id":h_data['id'],"ip":h_data['ip']}) 
                
                for h_path_data in self.path_data_heliostats:
                    status = ControlHelioStats.find_nearest_time_and_send(
                        self, list_path_data=h_path_data['path'], ip=h_path_data['ip']
                    )
                    if status['is_fail']:
                        print("Fail to send path data: " + f"{h_path_data['ip']}")
            else:
                for h_path_data in self.path_data_heliostats:
                    status = ControlHelioStats.find_nearest_time_and_send(
                        self, list_path_data=h_path_data['path'], ip=h_path_data['ip']
                    )
                    if status['is_fail']:
                        print("Fail to send path data: " + f"{h_path_data['ip']}")