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
import os
from os import listdir
from os.path import isfile, join
import requests
from kivy.app import App
from functools import partial


class PathControlWidget(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.list_data_helio = []
        self.list_data_cam = []
        self.helio_endpoint = ""
        self.camera_endpoint = ""
        self.camera_online_status= False
        Clock.schedule_once(lambda dt: self.fetch_all_helio_cam())
        Clock.schedule_once(lambda dt: self.fetch_list_file())
        # Clock.schedule_once(lambda dt: self.checking_menu())
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
    
    # def receive_text(self, text):
    #     app = App.get_running_app()
    #     current_mode = app.current_mode
    #     if self.menu_now != current_mode:
    #         self.call_close_camera()
    #         self.close_loop()
    #     else:
    #         self.checking_menu()
    #         # self.fetch_data_helio_stats()

    # def checking_menu(self):
    #     Clock.schedule_interval(self.receive_text, 1)

    # def close_loop(self):
    #     Clock.unschedule(self.receive_text)

    def send_file_selected(self,instance):
        headers = {}
        try:
            with open(self.path_file_selection, 'rb') as file:
            # Prepare the files dictionary for multipart/form-data
                files = {'file': (os.path.basename(self.path_file_selection), file, 'text/csv')}

            response = requests.post("http://"+self.helio_endpoint+"/update-path", files=files, headers=headers, timeout=30)

            if response.status_code == 200:
                self.show_popup("Success", "File uploaded successfully.")
                print("File uploaded successfully.")
            else:
                error_message = f"Failed to upload file. Status code: {response.status_code}\nResponse: {response.text}"
                self.show_popup("Upload Error", error_message)
                print(error_message)

        except Exception as e:
            print("error "+ "http://"+self.helio_endpoint+"/auto-data"+ " " + str(e))
            self.show_popup("Alert Error", e)

    def get_path_file(self, instance, path_file):
        self.path_file_selection = path_file
        # print(self.path_file_selection)
        self.show_popup("Alert", f"Path selected: {path_file}")

    def fetch_list_file(self):
        directory = "./data/result"
        try:
            self.list_file_path = [
                join(directory, f) for f in listdir(directory) if isfile(join(directory, f))
            ]
            # print(self.list_file_path)
        except FileNotFoundError:
            print(f"Directory {directory} does not exist.")
            self.list_file_path = []


    def show_popup_path_control(self):
        self.fetch_list_file()
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        btn_reload = Button(
            text="Reload",
            size_hint=(1, 0.1),
            on_press=self.reload_popup
        )
        layout.add_widget(btn_reload)
        scroll_view = ScrollView(size_hint=(1, 0.9))

        self.file_list_layout = BoxLayout(orientation="vertical", spacing=5, size_hint=(1, 0.9))
        self.populate_file_list()

        scroll_view.add_widget(self.file_list_layout)
        layout.add_widget(scroll_view)

        boxlayout_btn_send = BoxLayout(orientation="vertical", spacing=5, size_hint_y=.1)
        send_path_selection = Button(text="send path", on_press=self.send_file_selected)
        boxlayout_btn_send.add_widget(send_path_selection)
        layout.add_widget(boxlayout_btn_send)

        self.popup = Popup(
            title="Select Path Data",
            content=layout,
            size_hint=(0.8, 0.8),
            auto_dismiss=True 
        )
        self.popup.open()

    def populate_file_list(self):
        self.file_list_layout.clear_widgets()

        if not self.list_file_path:
            no_files_label = Label(text="No files found in ./data/result", size_hint=(1, 1))
            self.file_list_layout.add_widget(no_files_label)
            return

        for path in self.list_file_path:
            grid = GridLayout(cols=2, size_hint_y=None, height=50, spacing=10)
            label = Label(text=path, halign="left", valign="middle", size_hint=(0.8, 1))
            label.bind(size=label.setter('text_size'))  

            btn_select = Button(
                text="Select",
                size_hint=(0.2, 1)
            )
            btn_select.bind(on_press=lambda instance, p=path: self.get_path_file(instance, p))
            grid.add_widget(label)
            grid.add_widget(btn_select)
            self.file_list_layout.add_widget(grid)

    def reload_popup(self, instance):
        self.fetch_list_file()
        self.populate_file_list()

    def select_file(self, path):
        if self.popup:
            self.popup.dismiss()
    
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
                self.helio_endpoint = "http://"+h_data['ip']+"/update-datas"

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

    def call_open_camera(self):
        ###Initialize video capture and start updating frames.###
        if self.camera_online_status == False:
            print("ss")
            self.camera_online_status = True
            if self.camera_endpoint != "" and self.helio_endpoint != "":
                print("hjere1")
                if not self.capture:
                    try:
                        print("here 3")
                        self.capture = cv2.VideoCapture(self.camera_endpoint)
                        if not self.capture.isOpened():
                            self.show_popup("Error", "Could not open camera.")
                            return
                        # controller_manual =self.ids.controller_manual
                        self.ids.path_start_camera.text = "Camera off"
                        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
                    except Exception as e:
                        self.show_popup("Error camera", f"{e}")
            else: 
                self.show_popup("Alert", "Camera or helio stats must not empty.")   
        else:
            print("call_close_camera")
            # self.camera_online_status = False
            self.call_close_camera()

    def update_frame(self, dt):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                if len(self.selected_points) == 4:
                    frame = self.apply_perspective_transform(frame)
                    if frame is None:
                        return
                frame = cv2.flip(frame, 0)  # Flip frame vertically
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert frame to Kivy texture
                texture_rgb = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
                texture_rgb.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                self.ids.path_cam_image.texture = texture_rgb

    def call_close_camera(self):
        if self.capture!=None:
            self.camera_online_status = False
            self.capture.release()
            self.capture = None
            Clock.unschedule(self.update_frame)
            self.ids.path_start_camera.text = "Camera on"
            image_standby_path = "./images/sample_image_2.png"
            core_image = CoreImage(image_standby_path).texture
            self.ids.path_cam_image.texture = core_image
        else:
            pass

    def get_image_display_size_and_pos(self):
        ### Calculate the actual displayed image size and position within the widget.
        img_widget = self.ids.path_cam_image
        if not img_widget.texture:
            return None, None, None, None  # Texture not loaded yet

        # Original image size
        img_width, img_height = img_widget.texture.size
        # Widget size
        widget_width, widget_height = img_widget.size
        # Calculate scaling factor to fit the image within the widget while maintaining aspect ratio
        scale = min(widget_width / img_width, widget_height / img_height)
        # Calculate the size of the image as displayed
        display_width = img_width * scale
        display_height = img_height * scale
        # Calculate the position (bottom-left corner) of the image within the widget
        pos_x = img_widget.x + (widget_width - display_width) / 2
        pos_y = img_widget.y + (widget_height - display_height) / 2

        return display_width, display_height, pos_x, pos_y
    
    def map_touch_to_image_coords(self, touch_pos):
        ### Map touch coordinates to image pixel coordinates.
        display_width, display_height, pos_x, pos_y = self.get_image_display_size_and_pos()
        if display_width is None:
            return None, None  # Image not loaded

        x, y = touch_pos

        # Check if touch is within the image display area
        if not (pos_x <= x <= pos_x + display_width and pos_y <= y <= pos_y + display_height):
            return None, None  # Touch outside the image

        # Calculate relative position within the image display area
        rel_x = (x - pos_x) / display_width
        rel_y = (y - pos_y) / display_height

        # Get the actual image size
        img_width, img_height = self.ids.path_cam_image.texture.size

        # Map to image pixel coordinates
        img_x = int(rel_x * img_width)
        img_y = int((1 - rel_y) * img_height)  # Invert y-axis

        return img_x, img_y

    def on_touch_down(self, touch):
        ### Handle touch events for selecting points.### 
        img_widget = self.ids.path_cam_image
        if img_widget.collide_point(*touch.pos):
            # Check cropping mode
            try:
                with open('./data/setting/setting.json', 'r') as file:
                    setting_data = json.load(file)
            except Exception as e:
                self.show_popup("Error", f"Failed to load settings: {e}")
                return True

            if not setting_data.get('is_use_contour', False):
                # Polygon Cropping Mode
                if len(self.selected_points) >= 4:
                    self.show_popup("Info", "Already selected 4 points.")
                    return True

                # Map touch to image coordinates
                img_coords = self.map_touch_to_image_coords(touch.pos)
                if img_coords == (None, None):
                    self.show_popup("Error", "Touch outside the image area.")
                    return True

                img_x, img_y = img_coords
                self.selected_points.append((img_x, img_y))
                self.status_text = f"Selected {len(self.selected_points)} / 4 points."

                # Draw a small red circle at the touch point in image coordinates
                with img_widget.canvas.after:
                    Color(1, 0, 0, 1)  # Red color
                    d = 10.
                    # Convert back to widget coordinates for drawing
                    display_width, display_height, pos_x, pos_y = self.get_image_display_size_and_pos()
                    widget_x = pos_x + (img_x / img_widget.texture.width) * display_width
                    widget_y = pos_y + ((img_widget.texture.height - img_y) / img_widget.texture.height) * display_height
                    ellipse = Ellipse(pos=(widget_x - d/2, widget_y - d/2), size=(d, d))
                    self.point_markers.append(ellipse)

                # If four points are selected, draw the polygon
                if len(self.selected_points) == 4:
                    self.draw_polygon()

                return True
            else:
                # Rectangle Cropping Mode (existing functionality)
                self.dragging = True
                self.start_pos = touch.pos
                self.end_pos = touch.pos
                # Draw rectangle for visual feedback
                with self.ids.path_cam_image.canvas.after:
                    Color(1, 0, 0, 0.3)  # Red with transparency
                    self.rect = Rectangle(pos=self.start_pos, size=(0, 0))
                return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            self.show_popup("Error", f"Failed to load settings: {e}")
            return super().on_touch_move(touch)

        if not setting_data.get('is_use_contour', False):
            # Polygon Cropping Mode: No action on touch move
            return super().on_touch_move(touch)
        else:
            # Rectangle Cropping Mode
            if self.dragging:
                self.end_pos = touch.pos
                # Update rectangle size
                new_size = (self.end_pos[0] - self.start_pos[0], self.end_pos[1] - self.start_pos[1])
                self.rect.size = new_size
                return True
            return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        ###Handle touch up events.###
        img_widget = self.ids.path_cam_image
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            self.show_popup("Error", f"Failed to load settings: {e}")
            return super().on_touch_up(touch)

        if not setting_data.get('is_use_contour', False):
            # Polygon Cropping Mode: No action on touch up
            return super().on_touch_up(touch)
        else:
            # Rectangle Cropping Mode
            if self.dragging:
                self.dragging = False
                self.end_pos = touch.pos
                # Remove the rectangle from the canvas
                img_widget.canvas.after.remove(self.rect)
                self.rect = None
                # Calculate crop area
                self.calculate_crop_area()
                return True
            return super().on_touch_up(touch)

    def draw_polygon(self):
        ###Draw lines connecting the selected points to form a polygon.###
        img_widget = self.ids.path_cam_image

        # Get display size and position
        display_width, display_height, pos_x, pos_y = self.get_image_display_size_and_pos()

        # Convert image coordinates back to widget coordinates for drawing
        points = []
        for img_x, img_y in self.selected_points:
            widget_x = pos_x + (img_x / img_widget.texture.width) * display_width
            widget_y = pos_y + ((img_widget.texture.height - img_y) / img_widget.texture.height) * display_height
            points.extend([widget_x, widget_y])

        # Draw green lines connecting the points
        with img_widget.canvas.after:
            Color(0, 1, 0, 1)  # Green color
            self.polygon_lines = Line(points=points, width=2, close=True)
        self.remove_draw_point_marker()

    def order_points(self, pts):
        ###Order points in the order: top-left, top-right, bottom-right, bottom-left.###
        rect = np.zeros((4, 2), dtype="float32")

        # Sum and difference to find corners
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)

        rect[0] = pts[np.argmin(s)]      # Top-left has the smallest sum
        rect[2] = pts[np.argmax(s)]      # Bottom-right has the largest sum
        rect[1] = pts[np.argmin(diff)]   # Top-right has the smallest difference
        rect[3] = pts[np.argmax(diff)]   # Bottom-left has the largest difference

        return rect

    def is_valid_quadrilateral(self, pts):
        ###Check if the four points form a valid quadrilateral.###
        if len(pts) != 4:
            return False

        # Calculate the area using the shoelace formula
        area = 0.5 * abs(
            pts[0][0]*pts[1][1] + pts[1][0]*pts[2][1] +
            pts[2][0]*pts[3][1] + pts[3][0]*pts[0][1] -
            pts[1][0]*pts[0][1] - pts[2][0]*pts[1][1] -
            pts[3][0]*pts[2][1] - pts[0][0]*pts[3][1]
        )

        # Area should be positive and above a minimum threshold
        return area > 100  # Adjust the threshold as needed
    
    # if is_use_contour status active using this function #
    def apply_crop_methods(self, frame):

        with open('./data/setting/setting.json', 'r') as file:
            setting_data = json.load(file)

        M = np.array(setting_data['perspective_transform'])
        max_width = setting_data['max_width']
        max_height = setting_data['max_height']
        warped = cv2.warpPerspective(frame, M, (max_width, max_height))
        return warped

    def apply_perspective_transform(self, frame):
        ###Apply perspective transform based on selected polygon points.###
        if len(self.selected_points) != 4:
            self.show_popup("Error", "Exactly 4 points are required.")
            return frame  # Not enough points to perform transform

        # Order points: top-left, top-right, bottom-right, bottom-left
        pts = self.order_points(np.array(self.selected_points, dtype='float32'))

        if not self.is_valid_quadrilateral(pts):
            self.show_popup("Error", "Selected points do not form a valid quadrilateral.")
            return frame
        # print(pts)
        # Compute width and height of the new image
        width_a = np.linalg.norm(pts[0] - pts[1])
        width_b = np.linalg.norm(pts[2] - pts[3])
        max_width = max(int(width_a), int(width_b))

        height_a = np.linalg.norm(pts[0] - pts[3])
        height_b = np.linalg.norm(pts[1] - pts[2])
        max_height = max(int(height_a), int(height_b))
        # Destination points for perspective transform
        dst = np.array([
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1]
        ], dtype='float32')

        # Compute the perspective transform matrix
        M = cv2.getPerspectiveTransform(pts, dst)
        
        # update crop value
        self.perspective_transform = M
        self.max_width = max_width
        self.max_height = max_height
        

        warped = cv2.warpPerspective(frame, M, (max_width, max_height))
        return warped

    def fetch_status(self):
        ###Fetch settings from JSON and update UI accordingly.###
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            self.show_popup("Error", f"Failed to load settings: {e}")
            return

        # Update the status label based on 'is_use_contour'
        if not setting_data.get('is_use_contour', False):
            self.ids.using_crop_value_status.text = "Using Crop: Off"
        else:
            self.ids.using_crop_value_status.text = "Using Crop: On"

    def calculate_crop_area(self):
        ###Calculate and set the crop area for rectangle cropping.###
        if self.rect:
            pos = self.rect.pos
            size = self.rect.size
            x1, y1 = pos
            x2 = x1 + size[0]
            y2 = y1 + size[1]

            # Map widget coordinates to image coordinates
            display_width, display_height, pos_x, pos_y = self.get_image_display_size_and_pos()

            img_x1 = int((x1 - pos_x) / display_width * self.ids.path_cam_image.texture.width)
            img_y1 = int((self.ids.path_cam_image.texture.height - (y1 - pos_y) / display_height * self.ids.path_cam_image.texture.height))
            img_x2 = int((x2 - pos_x) / display_width * self.ids.path_cam_image.texture.width)
            img_y2 = int((self.ids.path_cam_image.texture.height - (y2 - pos_y) / display_height * self.ids.path_cam_image.texture.height))

            # Ensure coordinates are within image bounds
            img_x1 = max(0, min(img_x1, self.ids.path_cam_image.texture.width - 1))
            img_y1 = max(0, min(img_y1, self.ids.path_cam_image.texture.height - 1))
            img_x2 = max(0, min(img_x2, self.ids.path_cam_image.texture.width - 1))
            img_y2 = max(0, min(img_y2, self.ids.path_cam_image.texture.height - 1))
            
            self.crop_area = (min(img_x1, img_x2), min(img_y1, img_y2), max(img_x1, img_x2), max(img_y1, img_y2))

    def remove_draw_point_marker(self):
        # Clear point markers
        img_widget = self.ids.path_cam_image
        for marker in self.point_markers:
            img_widget.canvas.after.remove(marker)
        self.point_markers = []

        # Remove polygon lines
        if self.polygon_lines:
            img_widget.canvas.after.remove(self.polygon_lines)
            self.polygon_lines = None

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
        Clock.unschedule(self.fetch_data_helio_stats)

    def fetch_data_helio_stats(self, instance):
        # print("loop on")
        try:  
            data = requests.get("http://"+self.helio_endpoint)
            setJson = data.json()
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
            pass

        
    def haddle_start_run_path(self):
        if self.helio_endpoint != "":
            self.is_path_running = True
            try:
                with open("./data/setting/setting.json", 'r') as file:
                    setting_json = json.load(file)
                setting_json['is_run_path'] = 1

                payload = {
                    "topic":"mode",
                    "status":1,
                    "speed":setting_json['path_mode']['speed']
                }

                with open("./data/setting/setting.json", 'w') as file:
                    json.dump(setting_json, file, indent=4)
                headers={
                    'Content-Type': 'application/json'  
                }
                try:
                    response = requests.post("http://"+self.helio_stats_id_endpoint+"/auto-data", data=json.dumps(payload), headers=headers, timeout=5)
                    if response.status_code == 200:
                        self.show_popup("Alert connection error", response.status_code+"\n loop fetch data close")
                    else:
                        pass
                except Exception as e:
                    print("Connection error: "+str(e))
                    self.show_popup("Alert connection error", e+"\n loop fetch data close")
            except Exception as e:
                print(e)



    def haddle_stop_run_path(self):
        if self.helio_endpoint != "":
            self.is_path_running = False
            try:
                with open("./data/setting/setting.json", 'r') as file:
                    setting_json = json.load(file)
                setting_json['is_run_path'] = 1

                payload = {
                    "topic":"mode",
                    "status":0,
                    "speed":setting_json['path_mode']['speed']
                }

                with open("./data/setting/setting.json", 'w') as file:
                    json.dump(setting_json, file, indent=4)
                headers={
                    'Content-Type': 'application/json'  
                }
                try:
                    response = requests.post("http://"+self.helio_stats_id_endpoint+"/auto-data", data=json.dumps(payload), headers=headers, timeout=5)
                    if response.status_code == 200:
                        self.show_popup("Alert connection error", response.status_code+"\n loop fetch data close")
                    else:
                        pass
                except Exception as e:
                    print("Connection error: "+str(e))
                    self.show_popup("Alert connection error", e+"\n loop fetch data close")
            except Exception as e:
                print(e)

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
