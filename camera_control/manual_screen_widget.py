from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
import numpy as np
from kivy.graphics import Rectangle, Color
# import requests
# import time

class ManualScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capture = None
        self.dragging = False
        self.start_pos = (0, 0)
        self.end_pos = (0, 0)
        self.crop_area = None  # To store the crop area coordinates
        self.rect = None

    def on_touch_down(self, touch):
        img_widget = self.ids.manual_cam_image
        if img_widget.collide_point(*touch.pos):
            self.dragging = True
            self.start_pos = touch.pos
            self.end_pos = touch.pos
            # Draw rectangle for visual feedback
            with self.canvas:
                Color(1, 0, 0, 0.3)  # Red with transparency
                self.rect = Rectangle(pos=self.start_pos, size=(0, 0))
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            self.end_pos = touch.pos
            # Update rectangle size
            new_size = (self.end_pos[0] - self.start_pos[0], self.end_pos[1] - self.start_pos[1])
            self.rect.size = new_size
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            self.end_pos = touch.pos
            # Remove the rectangle from the canvas
            self.canvas.remove(self.rect)
            self.rect = None
            # Calculate crop area
            self.calculate_crop_area()
            return True
        return super().on_touch_up(touch)

    def calculate_crop_area(self):
        img_widget = self.ids.manual_cam_image
        widget_x, widget_y = img_widget.pos
        widget_width, widget_height = img_widget.size

        ret, frame = self.capture.read()
        if ret:
            img_height, img_width = frame.shape[:2]
            scale_x = img_width / widget_width
            scale_y = img_height / widget_height

            # Map start and end points to image coordinates
            start_x = (self.start_pos[0] - widget_x) * scale_x
            start_y = (self.start_pos[1] - widget_y) * scale_y
            end_x = (self.end_pos[0] - widget_x) * scale_x
            end_y = (self.end_pos[1] - widget_y) * scale_y

            # Adjust for Kivy's y-axis (bottom to top)
            start_y = img_height - start_y
            end_y = img_height - end_y

            # Ensure coordinates are within bounds and correctly ordered
            x1, x2 = sorted((int(max(0, min(start_x, end_x))), int(min(img_width, max(start_x, end_x)))))
            y1, y2 = sorted((int(max(0, min(start_y, end_y))), int(min(img_height, max(start_y, end_y)))))
            
            self.crop_area = (x1, y1, x2, y2)
            print(f"Crop area in image coordinates: {self.crop_area}")

    def find_bounding_boxes(self, gray_frame, blur_kernel, thresh_val, morph_kernel_size):
        blurred = cv2.GaussianBlur(gray_frame, blur_kernel, 0)
        _, thresh = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones(morph_kernel_size, np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours, thresh

    def calculate_centers(self, contours):
        centers = [(
            int(m['m10'] / m['m00']),
            int(m['m01'] / m['m00'])
        ) for cnt in contours if (m := cv2.moments(cnt))['m00'] != 0]
        if not centers:
            return [], []
        center_x, center_y = zip(*centers)
        return list(center_x), list(center_y)

    def call_open_camera(self):
        if not self.capture:
            video_path = "../test_target.mp4"  # Replace with 0 for webcam
            self.capture = cv2.VideoCapture(video_path)
            if not self.capture.isOpened():
                print("Error: Could not open camera.")
                self.ids.camera_status.text = "Error: Could not open camera"
                return
            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
            self.ids.camera_status.text = "Manual menu || camera status on"

    def update_frame(self, dt):
        

        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                # Apply cropping if crop_area is defined
                if self.crop_area:
                    x1, y1, x2, y2 = self.crop_area
                    frame = frame[y1:y2, x1:x2]
                    if frame.size == 0:
                        # print("Warning: Cropped frame is empty.")
                        return

                frame = cv2.flip(frame, 0)  # Flip frame vertically
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                # Find contours for frame and light targets
                contours_frame, _ = self.find_bounding_boxes(
                    frame_gray, blur_kernel=(5, 5), thresh_val=80, morph_kernel_size=(30, 30)
                )
                contours_light, _ = self.find_bounding_boxes(
                    frame_gray, blur_kernel=(55, 55), thresh_val=80, morph_kernel_size=(3, 3)
                )

                # Calculate centers
                centers_light = self.calculate_centers(contours_light)
                centers_frame = self.calculate_centers(contours_frame)

                total_centers = len(centers_light[0]) + len(centers_frame[0])

                if total_centers == 2:
                    bounding_box_frame_x = 0
                    bounding_box_frame_y = 0
                    bounding_box_frame_w = 0
                    bounding_box_frame_h = 0
                    # Draw centers and bounding boxes
                    for idx, (cx, cy) in enumerate(zip(centers_light[0], centers_light[1])):
                        cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

                    for idx, (cx, cy) in enumerate(zip(centers_frame[0], centers_frame[1])):
                        cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

                    for cnt in contours_light:
                        x, y, w, h = cv2.boundingRect(cnt)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                    for cnt in contours_frame:
                        x, y, w, h = cv2.boundingRect(cnt)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        bounding_box_frame_x = x
                        bounding_box_frame_y = y
                        bounding_box_frame_w = w
                        bounding_box_frame_h = h

                    # Convert frame to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Convert frame to Kivy texture
                    texture = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
                    texture.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                    self.ids.manual_cam_image.texture = texture

                    # Update UI labels
                    if centers_light[0] and centers_frame[0]:
                        self.ids.manual_center_target_position.text = f"X: {centers_light[0][0]}px Y: {centers_light[1][0]}px"
                        self.ids.manual_center_frame_position.text = f"X: {centers_frame[0][0]}px Y: {centers_frame[1][0]}px"
                        error_x = centers_frame[0][0] - centers_light[0][0]
                        error_y = centers_frame[1][0] - centers_light[1][0]
                        self.ids.manual_error_center.text = f"X: {error_x}px Y: {error_y}px"
                        self.ids.manual_bounding_frame_position.text = "X: " + str(bounding_box_frame_x)+"px" + " " + "Y: " + str(bounding_box_frame_y)+"px" + " " + "W: " + str(bounding_box_frame_w)+"px" + " " + "H: " + str(bounding_box_frame_h)+"px"
                else:
                    # Convert frame to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    texture = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
                    texture.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
                    self.ids.manual_cam_image.texture = texture

                    # Update UI labels with error
                    error_msg = f"Cannot detect target frame! Count targets: {total_centers}"
                    self.ids.manual_center_target_position.text = error_msg
                    self.ids.manual_center_frame_position.text = error_msg
                    self.ids.manual_bounding_frame_position.text = error_msg
                    self.ids.manual_error_center.text = error_msg

    def call_close_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None
            Clock.unschedule(self.update_frame)
            self.ids.camera_status.text = "Manual menu || camera status off"

    def cancel_crop(self):
        ### Cancels the current crop area selection and reverts to the original video frame.
        if self.crop_area:
            print("Crop area canceled.")
            self.crop_area = None
            # Optionally, update UI to reflect that cropping has been canceled
            self.ids.manual_center_target_position.text = "Crop canceled."
            self.ids.manual_center_frame_position.text = "Crop canceled."
            self.ids.manual_bounding_frame_position.text = "Crop canceled."
            self.ids.manual_error_center.text = "Crop canceled."
        
        if self.dragging:
            self.dragging = False
            if self.rect:
                self.canvas.remove(self.rect)
                self.rect = None

    def push_upper(self):
        print("Upper")

    def push_left(self):
        print("Left")

    def push_down(self):
        print("Down")

    def push_right(self):
        print("Right")