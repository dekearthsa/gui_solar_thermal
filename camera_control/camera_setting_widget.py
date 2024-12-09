from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
import cv2
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.label import Label
import numpy as np
from kivy.core.image import Image as CoreImage
import json
from kivy.uix.popup import Popup

class CameraSettingWidget(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.selected_points = []      # List to store selected points as (x, y) in image coordinates
        self.polygon_lines = None      # Line instruction for the polygon
        self.point_markers = []        # Ellipse instructions for points
        self.crop_area = None          # To store the crop area coordinates (if using rectangle)
        self.dragging = False          # Initialize dragging
        self.rect = None               # Initialize rectangle
        self.status_text = 'Ready'     # Initialize status text
        self.camera_connection = "rtsp://admin:Nu12131213@192.168.1.170:554/Streaming/Channels/101/"
        self.counting_number_crop = 0
        self.perspective_transform_top = []
        self.max_width_top = 0
        self.max_height_top = 0
        self.perspective_transform_bottom = []
        self.max_width_bottom = 0
        self.max_height_bottom = 0
        Clock.schedule_once(lambda dt: self.haddle_fetch_once_number_crop())

    def call_open_camera(self):
        ###Initialize video capture and start updating frames.###
        try:
            with open('./data/setting/setting.json') as file:
                setting_json = json.load(file)

            if setting_json['is_run_path'] != 1:
                if self.camera_connection != "":
                    if not self.capture:
                        try:
                            self.capture = cv2.VideoCapture(self.camera_connection, cv2.CAP_FFMPEG)
                            if not self.capture.isOpened():
                                self.show_popup("Error", "Could not open camera.")
                                self.ids.camera_setting_status.text = "Error: Could not open camera"
                                return
                            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
                            self.ids.camera_setting_status.text = "Camera status:On"
                        except Exception as e:
                            self.show_popup("Camera error", f"{e}")
                else:
                    self.show_popup("Alert", "Camera or helio stats must not empty.")
            else:
                self.show_popup("Alert", "Path system is running\n Stop path system to run ")
        except Exception as e:
            print(e)

    def update_frame(self, dt):
        if self.capture:
            ret, frame = self.capture.read()
            if len(self.selected_points) == 4 and self.counting_number_crop <= 2:
                self.counting_number_crop += 1
                self.apply_perspective_transform(frame)
            if ret:
                frame = cv2.flip(frame, 0)  # Flip frame vertically
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                texture_rgb = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
                texture_rgb.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                self.ids.camera_setting.texture = texture_rgb
                # print(self.counting_number_crop)
                if self.counting_number_crop == 1:
                    array_frame = self.convert_perspective_transform(frame)
                    # frame_top = cv2.flip(array_frame[0], 0)  # Flip frame vertically
                    
                    frame_rgb_top = cv2.cvtColor(array_frame[0], cv2.COLOR_BGR2RGB)
                    texture_rgb_top = Texture.create(size=(frame_rgb_top.shape[1], frame_rgb_top.shape[0]), colorfmt='rgb')
                    texture_rgb_top.blit_buffer(frame_rgb_top.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                    self.ids.camera_setting_bottom.texture = texture_rgb_top

                    
                elif self.counting_number_crop == 2:
                    array_frame = self.convert_perspective_transform(frame)
                    # frame_top = cv2.flip(array_frame[0], 0)  # Flip frame vertically
                    # frame_bottom = cv2.flip(array_frame[1], 0)  # Flip frame vertically

                    frame_rgb_top = cv2.cvtColor(array_frame[0], cv2.COLOR_BGR2RGB)
                    texture_rgb_top = Texture.create(size=(frame_rgb_top.shape[1], frame_rgb_top.shape[0]), colorfmt='rgb')
                    texture_rgb_top.blit_buffer(frame_rgb_top.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                    self.ids.camera_setting_bottom.texture = texture_rgb_top

                    frame_rgb_bottom = cv2.cvtColor(array_frame[1], cv2.COLOR_BGR2RGB)
                    texture_rgb_bottom = Texture.create(size=(frame_rgb_bottom.shape[1], frame_rgb_bottom.shape[0]), colorfmt='rgb')
                    texture_rgb_bottom.blit_buffer(frame_rgb_bottom.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                    self.ids.camera_setting_top.texture = texture_rgb_bottom

    def call_close_camera(self):
        # self.counting_number_crop = 0
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_json = json.load(file)
        except Exception as e:
            self.show_popup("Error", f"Failed to load settings: {e}")
        # setting_json['number_of_perspective_transform'] = 0
        try:
            with open('./data/setting/setting.json', 'w') as file:
                json.dump(setting_json, file, indent=4)
        except Exception as e:
            print(e)
            self.show_popup("Error", f'Error open file\n {e}')
        try:
            if self.capture:
                self.capture.release()
                self.capture = None
                Clock.unschedule(self.update_frame)
                image_standby_path = "./images/sample_image_2.png"
                core_image = CoreImage(image_standby_path).texture
                self.ids.camera_setting.texture = core_image
                self.ids.camera_setting_top.texture = core_image
                self.ids.camera_setting_bottom.texture = core_image
                self.ids.camera_setting_status.text = "camera status off"
        except:
            pass

    def get_image_display_size_and_pos(self):
        ### Calculate the actual displayed image size and position within the widget.
        img_widget = self.ids.camera_setting
        if not img_widget.texture:
            return None, None, None, None  # Texture not loaded yet
        img_width, img_height = img_widget.texture.size
        widget_width, widget_height = img_widget.size
        scale = min(widget_width / img_width, widget_height / img_height)
        display_width = img_width * scale
        display_height = img_height * scale
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
        img_width, img_height = self.ids.camera_setting.texture.size

        # Map to image pixel coordinates
        img_x = int(rel_x * img_width)
        img_y = int((rel_y) * img_height)  # Invert y-axis
        touch_y = int((1- rel_y) * img_height) 
        return img_x, img_y, touch_y 

    def on_touch_down(self, touch):
        ### Handle touch events for selecting points.### 
        img_widget = self.ids.camera_setting
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
                    self.show_popup("Info", "Reset selected points")
                    # self.selected_points = []
                    return True

                # Map touch to image coordinates
                img_coords = self.map_touch_to_image_coords(touch.pos)
                if img_coords == (None, None):
                    self.show_popup("Error", "Touch outside the image area.")
                    return True

                img_x, img_y, touch_y = img_coords
                self.selected_points.append((img_x, img_y))
                self.status_text = f"Selected {len(self.selected_points)} / 4 points."

                # Draw a small red circle at the touch point in image coordinates
                with img_widget.canvas.after:
                    Color(1, 0, 0, 1)  # Red color
                    d = 10.
                    # Convert back to widget coordinates for drawing
                    display_width, display_height, pos_x, pos_y = self.get_image_display_size_and_pos()
                    widget_x = pos_x + (img_x / img_widget.texture.width) * display_width
                    widget_y = pos_y + ((img_widget.texture.height - touch_y) / img_widget.texture.height) * display_height
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
                with self.ids.camera_setting.canvas.after:
                    Color(1, 0, 0, 0.3)  # Red with transparency
                    self.rect = Rectangle(pos=self.start_pos, size=(0, 0))
                return True
            
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        ### Handle touch move events for rectangle cropping.### 
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
        img_widget = self.ids.camera_setting
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
        img_widget = self.ids.camera_setting

        # Get display size and position
        display_width, display_height, pos_x, pos_y = self.get_image_display_size_and_pos()
        # print(display_width, display_height, pos_x, pos_y)
        # Convert image coordinates back to widget coordinates for drawing
        points = []
        
        for img_x, img_y in self.selected_points:
            widget_x = pos_x + (img_x / img_widget.texture.width) * display_width
            widget_y = pos_y + ((img_widget.texture.height - img_y) / img_widget.texture.height) * display_height
            points.extend([widget_x, widget_y])
        # print( , display_width, display_height)
        # Draw green lines connecting the points
        # print(points)
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
        print()
        warped = cv2.warpPerspective(frame, M, (max_width, max_height))
        return warped


    def convert_perspective_transform(self, frame):
        if self.counting_number_crop == 1:
            M_top = np.array(self.perspective_transform_top)
            max_width_top = self.max_width_top
            max_height_top = self.max_height_top
            frame_top = cv2.warpPerspective(frame, M_top, (max_width_top, max_height_top))
            return [frame_top]
        elif self.counting_number_crop == 2:
            M_top = np.array(self.perspective_transform_top)
            max_width_top = self.max_width_top
            max_height_top = self.max_height_top

            M_bottom = np.array(self.perspective_transform_bottom)
            max_width_bottom = self.max_width_bottom
            max_height_bottom = self.max_height_bottom

            frame_top = cv2.warpPerspective(frame, M_top, (max_width_top, max_height_top))
            frame_bottom = cv2.warpPerspective(frame, M_bottom, (max_width_bottom, max_height_bottom))
            return [frame_top,frame_bottom]


    def apply_perspective_transform(self, frame):
        ###Apply perspective transform based on selected polygon points.###
        pts = self.order_points(np.array(self.selected_points, dtype='float32'))
        if not self.is_valid_quadrilateral(pts):
            self.show_popup("Error", "Selected points do not form a valid quadrilateral.")
            return frame
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
        M = cv2.getPerspectiveTransform(pts, dst)
        self.selected_points = []
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_json = json.load(file)
        except Exception as e:
            self.show_popup("Error", f'Error open file\n {e}')
        if setting_json['number_of_perspective_transform'] <= 2:
            if self.counting_number_crop == 1:
                array_1d = []
                for value_list in M:
                    array_2d = []
                    for el in value_list:
                        array_2d.append(el)
                    array_1d.append(array_2d)
                setting_json['number_of_perspective_transform'] += 1
                setting_json['perspective_transform'] = array_1d
                setting_json['max_width'] = max_width
                setting_json['max_height'] = max_height
                self.perspective_transform_top = array_1d
                self.max_width_top = max_width
                self.max_height_top = max_height
                try:
                    with open('./data/setting/setting.json', 'w') as file:
                        json.dump(setting_json, file, indent=4)
                except Exception as e:
                    print(e)
                    self.show_popup("Error", f'Error open file\n {e}')

            elif self.counting_number_crop == 2:

                array_1d = []
                for value_list in M:
                    array_2d = []
                    for el in value_list:
                        array_2d.append(el)
                    array_1d.append(array_2d)
                
                setting_json['number_of_perspective_transform'] += 1
                setting_json['perspective_transform_bottom'] = array_1d
                setting_json['max_width_bottom'] = max_width
                setting_json['max_height_bottom'] = max_height
                self.perspective_transform_bottom = array_1d
                self.max_width_bottom = max_width
                self.max_height_bottom = max_height
                setting_json['crop_status'] = True
                try:
                    with open('./data/setting/setting.json', 'w') as file:
                        json.dump(setting_json, file, indent=4)
                except Exception as e:
                    print(e)
                    self.show_popup("Error", f'Error open file\n {e}')
        else:
            self.show_popup("Alert", "Camera setting finish \n Reset all crop press bottom reset.")

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

            img_x1 = int((x1 - pos_x) / display_width * self.ids.camera_setting.texture.width)
            img_y1 = int((self.ids.camera_setting.texture.height - (y1 - pos_y) / display_height * self.ids.camera_setting.texture.height))
            img_x2 = int((x2 - pos_x) / display_width * self.ids.camera_setting.texture.width)
            img_y2 = int((self.ids.camera_setting.texture.height - (y2 - pos_y) / display_height * self.ids.camera_setting.texture.height))

            # Ensure coordinates are within image bounds
            img_x1 = max(0, min(img_x1, self.ids.camera_setting.texture.width - 1))
            img_y1 = max(0, min(img_y1, self.ids.camera_setting.texture.height - 1))
            img_x2 = max(0, min(img_x2, self.ids.camera_setting.texture.width - 1))
            img_y2 = max(0, min(img_y2, self.ids.camera_setting.texture.height - 1))

            self.crop_area = (min(img_x1, img_x2), min(img_y1, img_y2), max(img_x1, img_x2), max(img_y1, img_y2))


    def remove_draw_point_marker(self):
        # Clear point markers
        img_widget = self.ids.camera_setting
        for marker in self.point_markers:
            img_widget.canvas.after.remove(marker)
        self.point_markers = []

        # Remove polygon lines
        if self.polygon_lines:
            img_widget.canvas.after.remove(self.polygon_lines)
            self.polygon_lines = None

    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(400, 200))
        popup.open()

    def haddle_reset_all_camera_setting(self):
        self.counting_number_crop = 0
        self.perspective_transform_top = []
        self.perspective_transform_bottom = []
        self.max_width_top = 0
        self.max_height_top = 0
        self.max_width_bottom = 0
        self.max_height_bottom = 0
        image_standby_path = "./images/sample_image_2.png"
        core_image = CoreImage(image_standby_path).texture
        self.ids.camera_setting_top.texture = core_image
        self.ids.camera_setting_bottom.texture = core_image

        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_json = json.load(file)
        except Exception as e:
            self.show_popup("Error", f"Failed to load settings: {e}")

        setting_json['number_of_perspective_transform'] = 0
        setting_json['is_use_contour'] = False
        setting_json['perspective_transform'] = [[0,0,0],[0,0,0],[0,0,0]]
        setting_json['max_width'] = 0
        setting_json['max_height'] = 0
        setting_json['perspective_transform_bottom'] = [[0,0,0],[0,0,0],[0,0,0]]
        setting_json['max_width_bottom'] = 0
        setting_json['max_height_bottom'] = 0
        setting_json['crop_status'] = False
        try:
            with open('./data/setting/setting.json', 'w') as file:
                json.dump(setting_json, file, indent=9)
        except Exception as e:
            print(e)
            self.show_popup("Error", f'Error open file\n {e}')
                    

    def haddle_fetch_once_number_crop(self):
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_json = json.load(file)
            self.counting_number_crop = setting_json['number_of_perspective_transform']

            self.perspective_transform_top = np.array(setting_json['perspective_transform'])
            self.max_width_top = setting_json['max_width']
            self.max_height_top = setting_json['max_height']

            self.perspective_transform_bottom = np.array(setting_json['perspective_transform_bottom'])
            self.max_width_bottom = setting_json['max_width_bottom']
            self.max_height_bottom = setting_json['max_height_bottom']
        except Exception as e:
            self.show_popup("error", f"{e}")

    def haddle_off_get_data(self):
        pass

    def stop_fetch_loop(self):
        pass

