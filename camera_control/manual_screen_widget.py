import json
import cv2
import numpy as np
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.core.image import Image as CoreImage
import requests
# import time

class ManualScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.selected_points = []      # List to store selected points as (x, y) in image coordinates
        self.polygon_lines = None      # Line instruction for the polygon
        self.point_markers = []        # Ellipse instructions for points
        self.crop_area = None          # To store the crop area coordinates (if using rectangle)

        self.perspective_transform = [[0,0,0], [0,0,0],[0,0,0]]
        self.max_width = 0
        self.max_height = 0
        
        self.reset_perspective_transform = [[0,0,0], [0,0,0],[0,0,0]]
        self.reset_max_width = 0
        self.reset_max_height = 0

        Clock.schedule_once(lambda dt: self.fetch_status()) # Fetch status is_use_contour from json setting file
        self.dragging = False          # Initialize dragging
        self.rect = None               # Initialize rectangle
        self.status_text = 'Ready'     # Initialize status text
        Clock.schedule_once(lambda dt: self.fetch_helio_stats_data())
        Clock.schedule_once(lambda dt: self.haddle_fetch_threshold_data())

        #### IN DEBUG MODE CHANGE THRES HERE ####
        self.static_low_h = 0 #10
        self.static_low_s = 0
        self.static_low_v = 180
        self.static_high_h = 179
        self.static_high_s = 255
        self.static_high_v = 255
        self.static_blur_kernel = (55,55) 
        self.static_min_area = 50000
        self.static_max_area = 130000
        # self.camera_connection = "vid_2.avi" ## path mp4 or camera url 
        # self.camera_connection = "rtsp://admin:Nu12131213@192.168.1.170:554/Streaming/Channels/101/"
        # "rtsp://admin:Nu12131213@192.168.1.170:554/Streaming/Channels/101/"
        # "rtsp://admin:NU12131213@192.168.1.171:554/Streaming/Channels/101/""
        self.camera_connection = ""
        self.helio_stats_connection = ""
        # self.start_time = time.time()

    def get_image_display_size_and_pos(self):
        ### Calculate the actual displayed image size and position within the widget.
        img_widget = self.ids.manual_cam_image
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
        img_width, img_height = self.ids.manual_cam_image.texture.size

        # Map to image pixel coordinates
        img_x = int(rel_x * img_width)
        img_y = int((1 - rel_y) * img_height)  # Invert y-axis

        return img_x, img_y

    def on_touch_down(self, touch):
        ### Handle touch events for selecting points.### 
        img_widget = self.ids.manual_cam_image
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
                with self.ids.manual_cam_image.canvas.after:
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
        img_widget = self.ids.manual_cam_image
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
        img_widget = self.ids.manual_cam_image

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

    def crop_image(self):
        ###Perform cropping based on selected mode.###
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_system = json.load(file)
        except Exception as e:
            self.show_popup("Error", f"Failed to load settings: {e}")
            return

        if not setting_system.get('is_use_contour', False):
            # Polygon Cropping Mode
            if len(self.selected_points) < 3:
                self.show_popup("Error", "Please select at least 3 points before cropping.")
                return

            # Load image using OpenCV
            img_path = self.image_source  # Ensure 'self.image_source' is correctly set
            image = cv2.imread(img_path)
            if image is None:
                self.show_popup("Error", f"Failed to load image: {img_path}")
                return

            # Create a mask with the same dimensions as the image
            mask = np.zeros(image.shape[:2], dtype=np.uint8)

            # Convert selected_points to a NumPy array of integer coordinates
            pts = np.array([self.selected_points], dtype=np.int32)

            # Fill the polygon on the mask
            cv2.fillPoly(mask, pts, 255)

            # Optionally, apply perspective transform if exactly 4 points are selected
            if len(self.selected_points) == 4:
                warped = self.apply_perspective_transform(image)
                if warped is None:
                    self.show_popup("Error", "Perspective transform failed.")
                    return
                # Apply mask to warped image
                mask_warped = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                warped_masked = cv2.bitwise_and(warped, warped, mask=mask_warped[:, :, 0])
                cropped_image = warped_masked
            else:
                # Apply mask to the original image
                cropped_image = cv2.bitwise_and(image, image, mask=mask)

            # Convert to BGRA to add alpha channel for transparency
            image_bgra = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2BGRA)
            image_bgra[:, :, 3] = mask  # Set alpha channel based on mask

            # Save the cropped image as PNG to preserve transparency
            cropped_path = 'images/cropped_image.png'
            cv2.imwrite(cropped_path, image_bgra)

            # Update the UI to display the cropped image
            self.image_source = cropped_path
            self.ids.manual_cam_image.source = cropped_path
            self.ids.manual_cam_image.reload()

            # Reset selections after cropping
            self.reset_selection()
            self.show_popup("Success", "Image cropped successfully!")

        else:
            # Rectangle Cropping Mode (existing functionality)
            if not self.crop_area:
                self.show_popup("Error", "No crop area selected.")
                return

            # Load image using OpenCV
            img_path = self.image_source  # Ensure 'self.image_source' is correctly set
            image = cv2.imread(img_path)
            if image is None:
                self.show_popup("Error", f"Failed to load image: {img_path}")
                return

            x1, y1, x2, y2 = self.crop_area
            cropped = image[y1:y2, x1:x2]

            # Save the cropped image
            cropped_path = 'images/cropped_image.jpg'
            cv2.imwrite(cropped_path, cropped)

            # Update the UI to display the cropped image
            self.image_source = cropped_path
            self.ids.manual_cam_image.source = cropped_path
            self.ids.manual_cam_image.reload()

            # Reset selections after cropping
            self.reset_selection()
            self.show_popup("Success", "Image cropped successfully!")

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

            img_x1 = int((x1 - pos_x) / display_width * self.ids.manual_cam_image.texture.width)
            img_y1 = int((self.ids.manual_cam_image.texture.height - (y1 - pos_y) / display_height * self.ids.manual_cam_image.texture.height))
            img_x2 = int((x2 - pos_x) / display_width * self.ids.manual_cam_image.texture.width)
            img_y2 = int((self.ids.manual_cam_image.texture.height - (y2 - pos_y) / display_height * self.ids.manual_cam_image.texture.height))

            # Ensure coordinates are within image bounds
            img_x1 = max(0, min(img_x1, self.ids.manual_cam_image.texture.width - 1))
            img_y1 = max(0, min(img_y1, self.ids.manual_cam_image.texture.height - 1))
            img_x2 = max(0, min(img_x2, self.ids.manual_cam_image.texture.width - 1))
            img_y2 = max(0, min(img_y2, self.ids.manual_cam_image.texture.height - 1))
            


            self.crop_area = (min(img_x1, img_x2), min(img_y1, img_y2), max(img_x1, img_x2), max(img_y1, img_y2))

    def remove_draw_point_marker(self):
        # Clear point markers
        img_widget = self.ids.manual_cam_image
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
        img_widget = self.ids.manual_cam_image
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

    def active_crop_value(self):
        ###Toggle the cropping mode between polygon and rectangle.###
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
        except Exception as e:
            self.show_popup("Error", f"Failed to load settings: {e}")
            return
        
        is_crop_full_frame = self.__recheck_perspective_transform(setting_data['perspective_transform'])

        if is_crop_full_frame == False:
            setting_data['is_use_contour'] = not setting_data.get('is_use_contour', False)
            try:
                with open('./data/setting/setting.json', 'w') as file:
                    json.dump(setting_data, file, indent=4)
            except Exception as e:
                self.show_popup("Error", f"Failed to save settings: {e}")
                return

        # Update the status label
        if not setting_data['is_use_contour']:
            self.ids.using_crop_value_status.text = "Using Crop: Off"
            self.reset_selection()
        else:
            self.ids.using_crop_value_status.text = "Using Crop: On"
            self.reset_selection()

    def reset_crop_value(self):
        ### Reset crop values to default in the settings JSON.###
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)

            setting_data['is_use_contour'] = False
            setting_data['perspective_transform'] = self.reset_perspective_transform
            setting_data['max_width'] = self.reset_max_width
            setting_data['max_height'] = self.reset_max_height

            with open('./data/setting/setting.json', 'w') as file:
                json.dump(setting_data, file, indent=4)
        except Exception as e:
            self.show_popup("Error", f"Failed to reset crop values: {e}")

    def save_crop_value_image(self):
        ###Save the current crop area to the settings JSON.###
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)

            array_1d = []
            for value_list in self.perspective_transform:
                array_2d = []
                for el in value_list:
                    array_2d.append(el)
                array_1d.append(array_2d)

            setting_data['perspective_transform'] = array_1d
            setting_data['max_width'] = self.max_width
            setting_data['max_height'] = self.max_height

            with open('./data/setting/setting.json', 'w') as file:
                json.dump(setting_data, file, indent=4)
        except Exception as e:
            self.show_popup("Error", f"Failed to save crop values: {e}")
    
    def find_bounding_boxes(self, gray_frame, blur_kernel, thresh_val, morph_kernel_size):

        blurred = cv2.GaussianBlur(gray_frame, blur_kernel, 0)
        _, thresh = cv2.threshold(blurred, thresh_val[0], thresh_val[1], cv2.THRESH_BINARY)
        kernel = np.ones(morph_kernel_size, np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
        return contours, thresh


    def __find_bounding_boxes_hsv_mode(self, frame_color, low_H, low_S, low_V, high_H, high_S, high_V, blur_kernel):
        frame_HSV = cv2.cvtColor(frame_color, cv2.COLOR_BGR2HSV)
        blurred = cv2.GaussianBlur(frame_HSV, blur_kernel, 0)
        frame_threshold = cv2.inRange(blurred, (low_H, low_S, low_V), (high_H, high_S, high_V))
        kernel_morph = np.ones((7,7), np.uint8)
        frame_morph = cv2.morphologyEx(frame_threshold, cv2.MORPH_OPEN, kernel_morph)
        contours_light, _ = cv2.findContours(
            frame_morph, 
            cv2.RETR_TREE, 
            cv2.CHAIN_APPROX_NONE
        )
        
        return contours_light, frame_threshold
    
    def calculate_centers(self, contours):
        ###Calculate the centers of the given contours.###
        centers = []
        for cnt in contours:
            M = cv2.moments(cnt)
            if M['m00'] != 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                centers.append((cx, cy))
        if not centers:
            return [], []
        center_x, center_y = zip(*centers)
        return list(center_x), list(center_y)
    
    def __calulate_centers_frame(self, frame):
        h, w = frame.shape[:2]
        center_x = w // 2
        center_y = h // 2
        center = (center_x, center_y)
        return center

    def call_open_camera(self):
        ###Initialize video capture and start updating frames.###
        if self.camera_connection != "" and self.helio_stats_connection != "":
            if self.camera_connection != "":
                if not self.capture:
                    # camera_connection = self.static_mp4  # For video file vid_1.avi, vid_2.avi
                    # camera_connection = "rtsp://admin:Nu12131213@192.168.1.170:554/Streaming/Channels/101/"  # Replace with your RTSP URL or use 0 for webcam
                    try:
                        self.capture = cv2.VideoCapture(self.camera_connection, cv2.CAP_FFMPEG)
                        if not self.capture.isOpened():
                            self.show_popup("Error", "Could not open camera.")
                            self.ids.camera_status.text = "Error: Could not open camera"
                            return
                        controller_manual =self.ids.controller_manual
                        controller_manual.camera_status_controll = "On"
                        Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
                        self.ids.camera_status.text = "Manual menu || Camera status:On"
                    except Exception as e:
                        self.show_popup("Camera error", f"{e}")
        else:
            self.show_popup("Alert", "Camera or helio stats must not empty.")

    def __recheck_perspective_transform(self,perspective):
        for el_array in  perspective:
            for val in el_array:
                if val != 0:
                    return False
                else:
                    pass
        return True

    def update_frame(self, dt):
        ### Read frames from the capture and process them.###
        if self.capture:
            ret, frame = self.capture.read()
            # debug_start = time.time()
            if ret:
                ### log time start here ###
                ### create image file ### 
                try:
                    with open('./data/setting/setting.json', 'r') as file:
                        setting_system = json.load(file)
                except Exception as e:
                    self.show_popup("Error", f"Failed to load settings: {e}")
                    return

                if not setting_system.get('is_use_contour', False):
                    # Polygon Cropping Mode
                    if len(self.selected_points) == 4:
                        # Apply perspective transform
                        frame = self.apply_perspective_transform(frame)
                        if frame is None:
                            return

                    frame = cv2.flip(frame, 0)  # Flip frame vertically

                    contours_light, demo_light = self.__find_bounding_boxes_hsv_mode(
                            frame_color=frame, 
                            low_H=self.static_low_h, 
                            low_S=self.static_low_s, 
                            low_V=self.static_low_v,
                            high_H=self.static_high_h,
                            high_S=self.static_high_s,
                            high_V=self.static_high_v,
                            blur_kernel=self.static_blur_kernel
                        )

                    # Calculate centers
                    centers_light = self.calculate_centers(contours_light)

                    ### using contours frame 
                    # centers_frame = self.calculate_centers(contours_frame)
                    ### calulate center of frame
                    centers_frame = self.__calulate_centers_frame(frame)

                    bounding_box_frame_x = centers_frame[0]
                    bounding_box_frame_y = centers_frame[1]
                    bounding_box_frame_w = setting_system['max_width']
                    bounding_box_frame_h = setting_system['max_height']
                    # static_min_area = 100
                    # Draw centers and bounding boxes
                    counting_light_center = 0
                    for idx, (cx, cy) in enumerate(zip(centers_light[0], centers_light[1])):
                        c_area = cv2.contourArea(contours_light[idx])
                        if self.static_min_area < c_area and self.static_max_area < c_area:
                            cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                            cv2.putText(frame, "C-L", (cx, cy + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

                    ### draw center of frame
                    cv2.circle(frame, centers_frame, 5,  (0, 255, 0), -1)
                    cv2.putText(frame, "C-F", centers_frame, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    for cnt in contours_light:
                        area = cv2.contourArea(cnt)
                        if self.static_min_area < c_area and self.static_min_area < area:
                            counting_light_center += 1
                            x, y, w, h = cv2.boundingRect(cnt)
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    # Convert frame to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # debug_stop = time.time()
                    # print(f"Time taken: {(debug_stop-debug_start)*10**3:.03f}ms")

                    # Convert frame to Kivy texture
                    texture_rgb = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
                    texture_rgb.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

                    texture_bin = Texture.create(size=(demo_light.shape[1], demo_light.shape[0]), colorfmt='luminance')
                    texture_bin.blit_buffer(demo_light.tobytes(), colorfmt='luminance', bufferfmt='ubyte')

                    self.ids.manual_cam_image.texture = texture_rgb
                    self.ids.manual_cam_image_demo.texture = texture_bin

                    # Update UI labels
                    if centers_light[0] and centers_frame[0]:
                        self.ids.number_of_center_light_detected.text = str(counting_light_center)
                        self.ids.description_of_center_light_count.text = self.__description_light_detected(counting_light_center)
                        self.ids.manual_center_target_position.text = f"X: {centers_light[0][0]}px Y: {centers_light[1][0]}px"
                        self.ids.manual_center_frame_position.text = f"X: {centers_frame[0]}px Y: {centers_frame[1]}px"
                        error_x = centers_frame[0] - centers_light[0][0]
                        error_y = centers_frame[1] - centers_light[1][0]
                        self.ids.manual_error_center.text = f"X: {error_x}px Y: {error_y}px"
                        self.ids.manual_bounding_frame_position.text = f"X: {bounding_box_frame_x}px Y: {bounding_box_frame_y}px W: {bounding_box_frame_w}px H: {bounding_box_frame_h}px"
                
                ### using crop data ###
                else:
                    try:
                        frame = self.apply_crop_methods(frame)
                        if frame.size == 0:
                            return
                        
                        frame = cv2.flip(frame, 0)  # Flip frame vertically
                        # frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                        ### ccc crop ###
                        # contours_light, demo_light = self.find_bounding_boxes(
                        #     frame_gray, blur_kernel=(55, 55), thresh_val=(120,135), morph_kernel_size=(3, 3)
                        # )

                        contours_light, demo_light = self.__find_bounding_boxes_hsv_mode(
                            frame_color=frame, 
                            low_H=self.static_low_h, 
                            low_S=self.static_low_s, 
                            low_V=self.static_low_v,
                            high_H=self.static_high_h,
                            high_S=self.static_high_s,
                            high_V=self.static_high_v,
                            blur_kernel=self.static_blur_kernel
                        )
                        
                        # Calculate centers
                        centers_light = self.calculate_centers(contours_light)
                        centers_frame = self.__calulate_centers_frame(frame)

                        bounding_box_frame_x = centers_frame[0]
                        bounding_box_frame_y = centers_frame[1]
                        bounding_box_frame_w = setting_system['max_width']
                        bounding_box_frame_h = setting_system['max_height']

                        # static_min_area = 0
                        # Draw centers and bounding boxes
                        counting_light_center = 0
                        for idx, (cx, cy) in enumerate(zip(centers_light[0], centers_light[1])):
                            c_area = cv2.contourArea(contours_light[idx])
                            if self.static_min_area < c_area and self.static_max_area > c_area:
                                cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)
                                cv2.putText(frame, "C-L", (cx, cy + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                        
                        ### draw center of frame
                        cv2.circle(frame, centers_frame, 5,  (0, 255, 0), -1)
                        cv2.putText(frame, "C-F", centers_frame, cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                        for cnt in contours_light:
                            area = cv2.contourArea(cnt)
                            if self.static_min_area < c_area and self.static_min_area < area:
                                counting_light_center += 1
                                x, y, w, h = cv2.boundingRect(cnt)
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                        # Convert frame to RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                        ### log stop time and delta time stop - start ### 

                        # Convert frame to Kivy texture
                        texture_rgb = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
                        texture_rgb.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

                        texture_bin = Texture.create(size=(demo_light.shape[1], demo_light.shape[0]), colorfmt='luminance')
                        texture_bin.blit_buffer(demo_light.tobytes(), colorfmt='luminance', bufferfmt='ubyte')

                        self.ids.manual_cam_image.texture = texture_rgb
                        self.ids.manual_cam_image_demo.texture = texture_bin

                        # Update UI labels
                        if centers_light[0] and centers_frame[0]:
                            self.ids.number_of_center_light_detected.text = str(counting_light_center)
                            self.ids.description_of_center_light_count.text = self.__description_light_detected(counting_light_center)
                            self.ids.manual_center_target_position.text = f"X: {centers_light[0][0]}px Y: {centers_light[1][0]}px"
                            self.ids.manual_center_frame_position.text = f"X: {centers_frame[0]}px Y: {centers_frame[1]}px"
                            error_x = centers_frame[0] - centers_light[0][0]
                            error_y = centers_frame[1] - centers_light[1][0]
                            self.ids.manual_error_center.text = f"X: {error_x}px Y: {error_y}px"
                            self.ids.manual_bounding_frame_position.text = f"X: {bounding_box_frame_x}px Y: {bounding_box_frame_y}px W: {bounding_box_frame_w}px H: {bounding_box_frame_h}px"
                            # debug_stop = time.time()
                            # print(f"Time taken: {(debug_stop-debug_start)*10**3:.03f}ms")
                    except Exception as e:
                        self.show_popup("Error", str(e))
                        return

    def __description_light_detected(self, number_center_light):
        if number_center_light == 1:
            return "Description: light detected status healthy!"
        elif number_center_light < 1:
            return "Description: not found light detected status unhealthy!"
        elif number_center_light > 1:
            return "Description: more than 1 found light detected status unhealthy!"

    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                    content=Label(text=message),
                    size_hint=(None, None), size=(400, 200))
        popup.open()

    def call_close_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None
            Clock.unschedule(self.update_frame)
            image_standby_path = "./images/sample_image_2.png"
            core_image = CoreImage(image_standby_path).texture
            self.ids.manual_cam_image.texture = core_image
            self.ids.manual_cam_image_demo.texture = core_image
            controller_manual =self.ids.controller_manual
            controller_manual.camera_status_controll = "Off"
            self.ids.camera_status.text = "Manual menu || camera status off"

    def fetch_helio_stats_data(self):
        with open('./data/setting/connection.json', 'r') as file:
            data = json.load(file)
        self.ids.spinner_helio_stats.values = [item['id'] for item in data.get('helio_stats_ip', [])]
        self.ids.spinner_camera.values = [item['id'] for item in data.get('camera_url', [])]
    
    def select_drop_down_menu_camera(self,spinner, text):
        self.call_close_camera()
        self.show_popup("Alert", "Camera change")
        self.ids.selected_label_camera.text = f"ID: {text}"
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
            
            for camera_name in storage['camera_url']:
                if text == camera_name['id']:
                    self.camera_connection =  camera_name['url']
        except Exception as e:
            self.show_popup("Error", f"{e}")

    def select_drop_down_menu_helio_stats(self, spinner, text):
        self.call_close_camera()
        self.show_popup("Alert", "Helio stats change")
        self.ids.selected_label_helio_stats.text = f"ID: {text}"
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
            
            for helio_stats in storage['helio_stats_ip']:
                if text == helio_stats['id']:
                    self.helio_stats_connection =  helio_stats['ip']
        except Exception as e:
            self.show_popup("Error", f"{e}")
    
    def haddle_fetch_threshold_data(self):
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            self.ids.slider_hsv_low_v.value = setting_data['hsv_threshold']['low_v']
            self.ids.set_step_machine.text = str(setting_data['control_speed_distance']['distance_mm'])
            self.ids.set_speed_machine.text = str(setting_data['control_speed_distance']['speed_screw'])
        except Exception as e:
            print(e)
            self.show_popup("Error file not found", f"Failed to load setting file {e}")

    def haddle_change_step_machine(self):
        step_input = self.ids.set_step_machine.text
        print(step_input)
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            setting_data['control_speed_distance']['distance_mm'] = int(step_input)

            with open("./data/setting/setting.json", "w") as file:
                json.dump(setting_data, file, indent=4)
        except Exception as e:
            print(e)
            self.show_popup("Error", f"Failed to upload value in setting file: {e}")


    def haddle_change_speed_machine(self):
        speed_input = self.ids.set_speed_machine.text
        try:
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            setting_data['control_speed_distance']['speed_screw'] = int(speed_input)

            with open("./data/setting/setting.json", "w") as file:
                json.dump(setting_data, file, indent=4)
        except Exception as e:
            print(e)
            self.show_popup("Error", f"Failed to upload value in setting file: {e}")

    def haddle_change_hsv_threshold(self, value): 
        try:
            self.static_low_v = value
            with open('./data/setting/setting.json', 'r') as file:
                setting_data = json.load(file)
            setting_data['hsv_threshold']['low_v'] = int(value)
            with open("./data/setting/setting.json", "w") as file:
                json.dump(setting_data, file, indent=4)
        except Exception as e:
            self.show_popup("Error", f"Failed to upload value in setting file: {e}")

    def haddle_reset_default_threshold(self):
        
        with open('./data/setting/setting.json', 'r') as file:
            setting_data = json.load(file)

        # setting_data['hsv_threshold']['low_v'] = 180 ## default low_v
        setting_data['control_speed_distance']['speed_screw'] = 100 ## default speed_screw
        setting_data['control_speed_distance']['distance_mm'] = 10  ## default distance_mm 

        with open("./data/setting/setting.json", "w") as file:
            json.dump(setting_data, file, indent=4)

        self.ids.slider_hsv_low_v.value = setting_data['hsv_threshold']['low_v']
        self.ids.set_step_machine.text = str(setting_data['control_speed_distance']['distance_mm'])
        self.ids.set_speed_machine.text = str(setting_data['control_speed_distance']['speed_screw'])

    def haddle_reset_default_threshold_low_v(self):
        with open('./data/setting/setting.json', 'r') as file:
            setting_data = json.load(file)
        
        setting_data['hsv_threshold']['low_v'] = 180 ## default low_v

        with open("./data/setting/setting.json", "w") as file:
            json.dump(setting_data, file, indent=4)
        
        self.ids.slider_hsv_low_v.value = setting_data['hsv_threshold']['low_v']

    def haddle_origin_x(self):
        if self.helio_stats_connection == "":
            self.show_popup("Error heliostats", "Not found heliostats connection!")
        else:
            payload =  {"topic": "origin", "axis": "x", "speed":400} 
            try:
                result = requests.post("http://"+self.helio_stats_connection +"/update-data", json=payload, timeout=5)
                print(result)
                # print(result.status_code)
                if result.status_code == 200:
                    self.show_popup("Alert", "set origin x success.")
                else:
                    self.show_popup("Error set origin x connection timeout: ", f"{result}")
            except Exception as e:
                self.show_popup("Error set origin x: ", f"{e}")

    def haddle_origin_y(self):
        if self.helio_stats_connection == "":
            self.show_popup("Error heliostats", "Not found heliostats connection!")
        else:
            payload =  {"topic": "origin", "axis": "y", "speed":400} 
            try:
                result = requests.post("http://"+self.helio_stats_connection +"/update-data", json=payload, timeout=5)
                print(result)
                if result.status_code == 200:
                    self.show_popup("Alert", "set origin y success.")
                else:
                    self.show_popup("Error set origin y connection timeout: ", f"{result}")
            except Exception as e:
                self.show_popup("Error set origin y: ", f"{e}")
