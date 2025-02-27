import json
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
import cv2
from kivy.graphics import Color, Ellipse, Line, Rectangle
import numpy as np
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput



import requests
from functools import partial
import subprocess

class PathControlWidget(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.list_data_helio = []
        self.list_data_cam = []
        self.helio_endpoint = ""
        self.helio_get_data = ""
        self.camera_endpoint = ""
        self.camera_online_status= False
        Clock.schedule_once(lambda dt: self.fetch_all_helio_cam())
        Clock.schedule_once(lambda dt: self.haddle_fetch_once())

        self.list_file_path = []
        self.capture = None
        self.selected_points = []      # List to store selected points as (x, y) in image coordinates
        self.polygon_lines = None      # Line instruction for the polygon
        self.point_markers = []        # Ellipse instructions for points
        self.crop_area = None          # To store the crop area coordinates (if using rectangle)
        self.dragging = False          # Initialize dragging
        self.rect = None               # Initialize rectangle
        self.status_text = 'Ready'     # Initialize status text
        self.popup = None  # To keep a reference to the popup
        self.path_file_selection = ""
        self.menu_now="path_control"
        self.is_path_running = False
        self.start_loop_get_data= False
        self.is_open_cam = False

        self.crop_status = False
        self.perspective_transform_top = []
        self.max_width_top = 0
        self.max_height_top = 0
        self.perspective_transform_bottom = []
        self.max_width_bottom = 0
        self.max_height_bottom = 0

    def haddle_fetch_once(self):
        with open('./data/setting/setting.json') as file:
            setting_json = json.load(file)
        self.perspective_transform_top = np.array(setting_json['perspective_transform'])
        self.max_width_top = setting_json['max_width']
        self.max_height_top = setting_json['max_height']

        self.perspective_transform_bottom = np.array(setting_json['perspective_transform_bottom'])
        self.max_width_bottom = setting_json['max_width_bottom']
        self.max_height_bottom = setting_json['max_height_bottom']

        self.crop_status = setting_json['crop_status']

    def convert_crop(self, frame):
        frame_top = cv2.warpPerspective(frame, self.perspective_transform_top, (self.max_width_top, self.max_height_top))
        frame_bottom = cv2.warpPerspective(frame, self.perspective_transform_bottom, (self.max_width_bottom, self.max_height_bottom))
        return frame_top, frame_bottom

    def open_web_upload(self, instance, endpoint):
        try:
            url="http://"+ str(endpoint.text)+ "/update-path"
            subprocess.run(["C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", url])
        except Exception as e:
            self.show_popup("File not found", f"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe \n ${e}")

    def show_popup_path_control(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        with open("./data/setting/connection.json", "r") as file:
            conn_file = json.load(file)
        for conn in conn_file['helio_stats_ip']:
            grid = GridLayout(cols=2, size_hint=(1, 1), height=40, spacing=10)
            
            label = Label(text="Helio ID " + conn['id'], size_hint=(1, .14))
            grid.add_widget(label)
        
            btn_open_wb = Button(text=str(conn['ip']), size_hint=(1, .14))
            # Correctly pass the IP string to the callback function
            btn_open_wb.bind(on_release=partial(self.open_web_upload, conn['ip']))
            grid.add_widget(btn_open_wb)
            layout.add_widget(grid)

        self.popup = Popup(
            title="Select Path Data",
            content=layout,
            size_hint=(0.8, 0.8),
            auto_dismiss=True 
        )
        self.popup.open()

    def fetch_all_helio_cam(self):
        with open('./data/setting/connection.json', 'r') as file:
            data = json.load(file)

        self.list_data_helio = data['helio_stats_ip']
        self.list_data_cam = data['camera_url']
        self.ids.spinner_helio_selection.values = [item['id'] for item in data.get('helio_stats_ip', [])]
        self.ids.spinner_camera_selection.values = [item['id'] for item in data.get('camera_url', [])]

    def select_drop_down_menu_helio_path(self, spinner, text):
        for h_data in self.list_data_helio:
            if text == h_data['id']:
                self.helio_endpoint = "http://"+h_data['ip']+"/update-data"
                self.helio_get_data = h_data['ip']

    def select_drop_down_menu_camera_path(self, spinner, text):
        for c_data in self.list_data_cam:
            if text ==  c_data['id']:
                self.camera_endpoint = c_data['url']

    def show_popup(self, title, message):
        ### Display a popup with a given title and message. ###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(800, 200))
        popup.open()

    def haddle_control_cam(self):
        if self.is_open_cam == False:
            self.is_open_cam = True
            self.call_open_camera()
        else:
            self.is_open_cam = False
            self.call_close_camera()

    def call_open_camera(self):
        ###Initialize video capture and start updating frames.###
        print(self.crop_status)
        if self.crop_status == True:
            if self.camera_endpoint != "" and self.helio_endpoint != "":
                print(self.camera_endpoint)
                print(self.helio_endpoint)
                if not self.capture:
                    try:
                        self.capture = cv2.VideoCapture(self.camera_endpoint)
                        if not self.capture.isOpened():
                            self.show_popup("Error", "Could not open camera.")
                            return
                        self.ids.path_start_camera.text = "Camera off"
                        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
                    except Exception as e:
                        self.show_popup("Error camera", f"{e}")
            else: 
                self.show_popup("Alert", "Camera or helio stats must not empty.")   
        else:
            self.show_popup("Alert", "Camera not setting.") 

    def update_frame(self, dt):
        if self.capture:
            ret, frame = self.capture.read()
            frame = cv2.flip(frame, 0) 
            if ret:
                frame_top , frame_bottom = self.convert_crop(frame)

                frame_rgb_top = cv2.cvtColor(frame_top, cv2.COLOR_BGR2RGB)
                texture_rgb_top = Texture.create(size=(frame_rgb_top.shape[1], frame_rgb_top.shape[0]), colorfmt='rgb')
                texture_rgb_top.blit_buffer(frame_rgb_top.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                self.ids.path_cam_image_top.texture = texture_rgb_top

                frame_rgb_bottom = cv2.cvtColor(frame_bottom, cv2.COLOR_BGR2RGB)
                texture_rgb_bottom = Texture.create(size=(frame_rgb_bottom.shape[1], frame_rgb_bottom.shape[0]), colorfmt='rgb')
                texture_rgb_bottom.blit_buffer(frame_rgb_bottom.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                self.ids.path_cam_image.texture = texture_rgb_bottom

    def call_close_camera(self):
        try:
            if self.capture!=None:
                self.camera_online_status = False
                self.capture.release()
                self.capture = None
                Clock.unschedule(self.update_frame)
                self.ids.path_start_camera.text = "Camera on"

                image_standby_path = "./images/sample_image_2.png"
                core_image = CoreImage(image_standby_path).texture
                self.ids.path_cam_image.texture = core_image
                self.ids.path_cam_image_top.texture = core_image
            else:
                pass
        except:
            pass

    def reset_selection(self):
        ###Reset the selected points and clear drawings.###
        self.selected_points = []
        self.status_text = 'Selection reset. Select points by clicking on the image.'

        # Clear point markers
        img_widget = self.ids.path_cam_image
        for marker in self.point_markers:
            img_widget.canvas.after.remove(marker)
        self.point_markers = []

        # Remove polygon lines
        if self.polygon_lines:
            img_widget.canvas.after.remove(self.polygon_lines)
            self.polygon_lines = None

        # Clear rectangle if in rectangle mode
        if hasattr(self, 'rect') and self.rect:
            img_widget.canvas.after.remove(self.rect)
            self.rect = None

    def haddle_btn_get_data(self): 
        if self.start_loop_get_data == False:
            self.start_loop_get_data = True
            self.ids.get_data_helio.text = "Off get data"
            self.haddle_start_get_data()
        else:
            self.start_loop_get_data = False
            self.ids.get_data_helio.text = "On get data"
            self.haddle_off_get_data()

    def haddle_start_get_data(self):
        Clock.schedule_interval(self.fetch_data_helio_stats, 1)

    def haddle_off_get_data(self):
        try:
            Clock.unschedule(self.fetch_data_helio_stats)
        except:
            pass
        

    def fetch_data_helio_stats(self, instance):
        # print("loop on")
        try:  
            # print(self.helio_get_data)
            data = requests.get("http://"+self.helio_get_data+"/",timeout=3)
            # data = requests.get("http://"+"192.168.0.106"+"/")
            # data = requests.get(url="http://192.168.0.106/")
            
            setJson = data.json()
            # print(setJson)
            self.ids.val_id.text = str(setJson['id'])
            self.ids.val_currentX.text = str(setJson['currentX'])
            self.ids.val_currentY.text = str(setJson['currentY'])
            self.ids.val_err_posx.text = str(setJson['err_posx'])
            self.ids.val_err_posy.text = str(setJson['err_posy'])
            self.ids.val_x.text= str(setJson['safety']['x'])
            self.ids.val_y.text= str(setJson['safety']['y'])
            self.ids.val_x1.text= str(setJson['safety']['x1'])
            self.ids.val_y1.text= str(setJson['safety']['y1'])
            self.ids.val_ls1.text= str(setJson['safety']['ls1'])
            self.ids.val_st_path.text= str(setJson['safety']['st_path'])
            self.ids.val_move_comp.text= str(setJson['safety']['move_comp'])
            self.ids.val_elevation.text= str(setJson['elevation'])
            self.ids.val_azimuth.text= str(setJson['azimuth'])
        except Exception as e:
            print(f"error connection {e}")
            self.show_popup("Alert", "connection error close get data.")
            self.haddle_off_get_data()

        
    def haddle_start_run_path(self):
        print("run path")
        print(self.helio_endpoint)
        if self.helio_endpoint != "":
            self.is_path_running = True
            try:
                with open("./data/setting/setting.json", 'r') as file:
                    setting_json = json.load(file)
                setting_json['is_run_path'] = 1

                payload = {
                    "topic":"mode",
                    "status":1,
                    "speed":setting_json['control_speed_distance']['path_mode']['speed']
                }
                print(payload)

                with open("./data/setting/setting.json", 'w') as file:
                    json.dump(setting_json, file, indent=4)
                headers={
                    'Content-Type': 'application/json'  
                }
                try:
                    print(self.helio_endpoint)
                    print(payload)
                    response = requests.post(self.helio_endpoint, data=json.dumps(payload), headers=headers, timeout=3)
                    # print(response)
                    if response.status_code != 200:
                        print(response.status_code)
                        self.show_popup("Alert connection error", "error connection loop fetch data close")
                    else:
                        self.show_popup("Alert", "Path controll on")
                        pass

                except Exception as e:
                    self.show_popup("Alert connection error", " loop fetch data close")
                    print("connection fail => ",e)
                    
            except Exception as e:
                print("error =>",e)



    def haddle_stop_run_path(self):
        # print("run path")
        # print(self.helio_endpoint)
        if self.helio_endpoint != "":
            self.is_path_running = True
            try:
                with open("./data/setting/setting.json", 'r') as file:
                    setting_json = json.load(file)
                setting_json['is_run_path'] = 0

                payload = {
                    "topic":"mode",
                    "status":0,
                    "speed":setting_json['control_speed_distance']['path_mode']['speed']
                }
                print(payload)

                with open("./data/setting/setting.json", 'w') as file:
                    json.dump(setting_json, file, indent=4)
                headers={
                    'Content-Type': 'application/json'  
                }
                try:
                    print(self.helio_endpoint)
                    print(payload)
                    response = requests.post(self.helio_endpoint, data=json.dumps(payload), headers=headers, timeout=5)
                    # print(response)
                    if response.status_code != 200:
                        print(response.status_code)
                        self.show_popup("Alert connection error", "error connection loop fetch data close")
                    else:
                        self.show_popup("Alert", "Path controll off")
                        pass
                except Exception as e:
                    print(e)
                    self.show_popup("Alert connection error", " loop fetch data close")
            except Exception as e:
                print("error =>",e)

    def haddle_update_speed(self, text_input, instance):
        val = text_input.text.strip()
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            setting_data['control_speed_distance']['path_mode']['speed'] = int(val)
            with open('./data/setting/setting.json', 'w') as file_save:
                json.dump(setting_data, file_save, indent=4)
        except Exception as e:
            self.show_popup("Error", f"Failed to reset crop values: {e}")

    def haddle_config_path(self):
        with open('./data/setting/setting.json', 'r') as file:
            setting_data = json.load(file) 

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        grid = GridLayout(cols=3, size_hint=(1, 1), height=40, spacing=10)
        # Label
        label = Label(text="Path speed", size_hint=(0.3, 1))
        grid.add_widget(label)

        # TextInput
        text_input =  TextInput(text=str(setting_data['control_speed_distance']['path_mode']['speed']),
                    hint_text="Enter speed",
                    multiline=False,
                    size_hint=(.3, 1)
                )
        grid.add_widget(text_input)

        # Update Button
        update_btn = Button(text='Update', size_hint=(0.2, 1))
        # Bind the Update button to the respective handler with TextInput
        update_btn.bind(on_release=partial(self.haddle_update_speed, text_input))
        grid.add_widget(update_btn)

        # Add the GridLayout to the main layout
        layout.add_widget(grid)
        # Create the Popup
        popup = Popup(
            title="config path parameter",
            content=layout,
            size_hint=(None, .12),
            size=(850, 190),
            auto_dismiss=True  # Allow dismissal by clicking outside or pressing Escape
        )
        popup.open()

    def stop_fetch_loop(self):
        pass