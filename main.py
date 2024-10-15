from kivy.uix.actionbar import Label
from kivy.app import App
from kivy.metrics import dp

from kivy.uix.pagelayout import PageLayout
from kivy.uix.dropdown import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.gridlayout import GridLayout

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.graphics import Rectangle, Color
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ListProperty
from kivy.core.window import Window

### from kivy.core.window import Window ### windows fix 
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
import requests
import time
import numpy as np
import json 


class ManualScreen(Screen):
    def __init__(self, **kwargs):
        super(ManualScreen, self).__init__(**kwargs)
        self.capture = None
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.crop_area = None  # To store the crop area coordinates
        self.rect = None  

    def call_open_camera(self):
        if not self.capture:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                print("Error: Could not open camera.")
                self.ids.camera_status.text = "Error: Could not open camera"
                return
            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
            self.ids.camera_status.text = "Manual menu || camera status on"

    def on_touch_down(self, touch):
        if self.ids.manual_cam_image.collide_point(*touch.pos):
            self.dragging = True
            self.start_x, self.start_y = touch.pos
            self.end_x, self.end_y = touch.pos
            # Draw rectangle for visual feedback
            with self.canvas:
                Color(1, 0, 0, 0.3)  # Red with transparency
                self.rect = Rectangle(pos=(self.start_x, self.start_y), size=(0, 0))
            return True
        return super(ManualScreen, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            self.end_x, self.end_y = touch.pos
            # Update rectangle size
            self.rect.size = (self.end_x - self.start_x, self.end_y - self.start_y)
            return True
        return super(ManualScreen, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            self.end_x, self.end_y = touch.pos
            # Remove the rectangle from the canvas
            self.canvas.remove(self.rect)
            self.rect = None
            # Calculate crop area
            self.calculate_crop_area()
            return True
        return super(ManualScreen, self).on_touch_up(touch)


    def calculate_crop_area(self):
        # Get the image widget
        img_widget = self.ids.manual_cam_image
        # Get the widget position and size
        widget_x, widget_y = img_widget.pos
        widget_width, widget_height = img_widget.size
        # Get the frame size
        ret, frame = self.capture.read()
        if ret:
            img_height, img_width = frame.shape[:2]
            # Calculate scaling factors
            scale_x = img_width / widget_width
            scale_y = img_height / widget_height

            # Map start and end points to image coordinates
            start_x = (self.start_x - widget_x) * scale_x
            start_y = (self.start_y - widget_y) * scale_y
            end_x = (self.end_x - widget_x) * scale_x
            end_y = (self.end_y - widget_y) * scale_y

            # Adjust for coordinate system difference (Kivy's y-axis is bottom to top)
            start_y = img_height - start_y
            end_y = img_height - end_y

            # Ensure coordinates are within bounds
            x1 = int(max(0, min(start_x, end_x)))
            y1 = int(max(0, min(start_y, end_y)))
            x2 = int(min(img_width, max(start_x, end_x)))
            y2 = int(min(img_height, max(start_y, end_y)))

            self.crop_area = (x1, y1, x2, y2)
            print(f"Crop area in image coordinates: {self.crop_area}")

    def find_bounding_box_frame(self,gray_frame):
        ### if no crop system ###
        ### remove noise ###
        # blurred = cv2.GaussianBlur(gray_frame, (85,85), 0)
        # _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # kernel = np.ones((300, 300), np.uint8)
        # thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        ### if crop system ###
        ### remove noise ###
        blurred = cv2.GaussianBlur(gray_frame, (5,5), 0)
        _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((30, 30), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        ### end config noise frame ###
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours, thresh
    
    def find_bounding_box_light(self,gray_frame):
        ### config noise target ###
        blurred = cv2.GaussianBlur(gray_frame, (55, 55), 0) ## Gaussian blur to reduce noise
        _, thresh = cv2.threshold(blurred, 180, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        ### end config noise target ###
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours, thresh
    
    def calculate_center(self, contours):
        array_center_x = []
        array_center_y = []
        for i in contours: 
            m = cv2.moments(i)
            if m['m00'] != 0:
                cx = int(m['m10']/m['m00'])
                cy = int(m['m01']/m['m00'])
                array_center_x.append(cx)
                array_center_y.append(cy)
        return (array_center_x, array_center_y)

    def update_frame(self, dt):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                # Flip the frame if necessary
                # frame = cv2.flip(frame, 0)

                # Apply cropping if crop_area is defined
                if self.crop_area:
                    x1, y1, x2, y2 = self.crop_area
                    frame = frame[y1:y2, x1:x2]
                    if frame.size == 0:
                        # print("Warning: Cropped frame is empty.")
                        return

                # Now proceed with your existing image processing
                # For example:
                # image = cv2.imread('/Users/pcsishun/project_solar_thermal/gui_solar_control/test9.png')
                frame = cv2.flip(frame, 0) # flip frame
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                ### convert frame to black and white
                contours_frame, debug_thresh_frame = self.find_bounding_box_frame(frame_gray)
                contours_light, debug_thresh_light = self.find_bounding_box_light(frame_gray)

                ### find the center of frame ###
                center_x_light, center_y_light = self.calculate_center(contours_light)
                center_x_frame, center_y_frame = self.calculate_center(contours_frame)

                ### draw main center of target ###
                center_color_target = 0
                for idx,el in  enumerate(center_x_light):
                    cv2.circle(frame, (center_x_light[idx], center_y_light[idx]), 14,(255,0,center_color_target),-1 )
                    # cv2.putText(frame, "center_x_light: "+ str(center_x_light[idx]) + " " + "center_y_light: "+str(center_y_light[idx]) ,(center_x_light[idx] - 200, center_y_light[idx] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,center_color_target), 3)
                    center_color_target += 100
                    x_center_light = center_x_light[idx]
                    y_center_light = center_y_light[idx]

                ### draw main center of frame ###
                center_color_frame = 0
                for idx,el in  enumerate(center_x_frame):
                    cv2.circle(frame, (center_x_frame[idx], center_y_frame[idx]), 14,(0,255,center_color_frame),-1 )
                    # cv2.putText(frame, "center_x_frame: "+ str(center_x_frame[idx]) + " " + "center_y_frame: "+str(center_y_frame[idx]) ,(center_x_frame[idx], center_y_frame[idx] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,center_color_frame), 3)
                    center_color_frame += 100
                    x_center_frame = center_x_frame[idx]
                    y_center_frame = center_y_frame[idx]

                ### draw bounding box of target ###
                area_color_target = 0
                for cnt in contours_light:
                    x,y,w,h = cv2.boundingRect(cnt)
                    # cv2.putText(frame, "X:"+str(x) + " " + "Y:"+str(y) +" "+ "W:"+str(w) +" "+ "H:"+str(h),(x,y+50), cv2.FONT_HERSHEY_SIMPLEX, 1,  (255,0,area_color_target), 4)
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),10)
                    area_color_target += 100

                ### draw bounding box of frame ###
                area_color_bounding_box_frame = 0
                for cnt in contours_frame:
                    x,y,w,h = cv2.boundingRect(cnt)
                    # cv2.putText(frame, "X:"+str(x) + " " + "Y:"+str(y) +" "+ "W:"+str(w) +" "+ "H:"+str(h),(x,y+50), cv2.FONT_HERSHEY_SIMPLEX, 1,  (0,255,area_color_bounding_box_frame), 4)
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,area_color_bounding_box_frame),10)
                    area_color_bounding_box_frame += 100
                    bounding_box_frame_x = x
                    bounding_box_frame_y = y
                    bounding_box_frame_w = w
                    bounding_box_frame_h = h

                ### warp all draw in same image frame ### 
                frame_with_contours = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                ### convert frame to kivy texture ###
                buffer = frame_with_contours.tobytes()
                convert_frame_to_kivy = Texture.create(size=(frame_with_contours.shape[1], frame_with_contours.shape[0]), colorfmt='rgb')
                convert_frame_to_kivy.blit_buffer(buffer, colorfmt='rgb', bufferfmt='ubyte') # luminance
                
                ### send frame to frontend ###
                self.ids.manual_cam_image.texture = convert_frame_to_kivy
                self.ids.manual_center_target_position.text = "X: " + str(center_x_light[0])+"px"+ " " + "Y: " + str(center_y_light[0])+"px" ### light center target must have 1 center
                self.ids.manual_center_frame_position.text =  "X: "+  str(center_x_frame[0])+"px"+ " " + "Y: " + str(center_y_frame[0])+"px" ### frame center target must have 1 center
                self.ids.manual_bounding_frame_position.text =  "X: " + str(bounding_box_frame_x)+"px" + " " + "Y: " + str(bounding_box_frame_y)+"px" + " " + "W: " + str(bounding_box_frame_w)+"px" + " " + "H: " + str(bounding_box_frame_h)+"px"
                self.ids.manual_error_center.text = "X: " + str(x_center_frame - x_center_light)+"px" + " " + "Y: " + str(y_center_frame - y_center_light) + "px"

    def call_close_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None
            Clock.unschedule(self.update_frame)
            self.ids.camera_status.text = "Manual menu || camera status off"

    def push_upper(self):
        print("Upper")

    def push_left(self):
        print("Left")

    def push_down(self):
        print("Down")

    def push_right(self):
        print("Right")

class SetAutoScreen(Screen):
    def __init__(self, **kwargs):
        super(SetAutoScreen, self).__init__(**kwargs)
        self.capture = None
        self.dragging = False
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.crop_area = None  # To store the crop area coordinates
        self.rect = None  

    def call_open_camera(self):
        if not self.capture:
            self.capture = cv2.VideoCapture(0)
            if not self.capture.isOpened():
                print("Error: Could not open camera.")
                self.ids.camera_status_auto_mode.text = "Error: Could not open camera"
                return
            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
            self.ids.camera_status_auto_mode.text = "Auto menu || camera status on"

    def on_touch_down(self, touch):
        if self.ids.auto_cam_image.collide_point(*touch.pos):
            self.dragging = True
            self.start_x, self.start_y = touch.pos
            self.end_x, self.end_y = touch.pos
            # Draw rectangle for visual feedback
            with self.canvas:
                Color(1, 0, 0, 0.3)  # Red with transparency
                self.rect = Rectangle(pos=(self.start_x, self.start_y), size=(0, 0))
            return True
        return super(SetAutoScreen, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.dragging:
            self.end_x, self.end_y = touch.pos
            # Update rectangle size
            self.rect.size = (self.end_x - self.start_x, self.end_y - self.start_y)
            return True
        return super(SetAutoScreen, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.dragging:
            self.dragging = False
            self.end_x, self.end_y = touch.pos
            # Remove the rectangle from the canvas
            self.canvas.remove(self.rect)
            self.rect = None
            # Calculate crop area
            self.calculate_crop_area()
            return True
        return super(SetAutoScreen, self).on_touch_up(touch)

    def calculate_crop_area(self):
        # Get the image widget
        img_widget = self.ids.auto_cam_image
        # Get the widget position and size
        widget_x, widget_y = img_widget.pos
        widget_width, widget_height = img_widget.size
        # Get the frame size
        ret, frame = self.capture.read()
        if ret:
            img_height, img_width = frame.shape[:2]
            # Calculate scaling factors
            scale_x = img_width / widget_width
            scale_y = img_height / widget_height

            # Map start and end points to image coordinates
            start_x = (self.start_x - widget_x) * scale_x
            start_y = (self.start_y - widget_y) * scale_y
            end_x = (self.end_x - widget_x) * scale_x
            end_y = (self.end_y - widget_y) * scale_y

            # Adjust for coordinate system difference (Kivy's y-axis is bottom to top)
            start_y = img_height - start_y
            end_y = img_height - end_y

            # Ensure coordinates are within bounds
            x1 = int(max(0, min(start_x, end_x)))
            y1 = int(max(0, min(start_y, end_y)))
            x2 = int(min(img_width, max(start_x, end_x)))
            y2 = int(min(img_height, max(start_y, end_y)))

            self.crop_area = (x1, y1, x2, y2)
            print(f"Crop area in image coordinates: {self.crop_area}")

    def find_bounding_box_frame(self, gray_frame):
        ### if no crop system ###
        ### remove noise ###
        # blurred = cv2.GaussianBlur(gray_frame, (85,85), 0)
        # _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # kernel = np.ones((300, 300), np.uint8)
        # thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        ### if crop system ###
        ### remove noise ###
        blurred = cv2.GaussianBlur(gray_frame, (5,5), 0)
        _, thresh = cv2.threshold(blurred, 160, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((30, 30), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        ### end config noise frame ###
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours, thresh
    
    def find_bounding_box_light(self, gray_frame):
        ### config noise target ###
        blurred = cv2.GaussianBlur(gray_frame, (55, 55), 0)  # Gaussian blur to reduce noise
        _, thresh = cv2.threshold(blurred, 180, 255, cv2.THRESH_BINARY)
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        ### end config noise target ###
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours, thresh
    
    def calculate_center(self, contours):
        array_center_x = []
        array_center_y = []
        for i in contours: 
            m = cv2.moments(i)
            if m['m00'] != 0:
                cx = int(m['m10'] / m['m00'])
                cy = int(m['m01'] / m['m00'])
                array_center_x.append(cx)
                array_center_y.append(cy)
        return (array_center_x, array_center_y)

    def update_frame(self, dt):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                # Flip the frame if necessary
                # frame = cv2.flip(frame, 0)

                # Apply cropping if crop_area is defined
                if self.crop_area:
                    x1, y1, x2, y2 = self.crop_area
                    frame = frame[y1:y2, x1:x2]
                    if frame.size == 0:
                        # print("Warning: Cropped frame is empty.")
                        return

                # Now proceed with your existing image processing
                frame = cv2.flip(frame, 0)  # flip frame
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                ### convert frame to black and white
                contours_frame, debug_thresh_frame = self.find_bounding_box_frame(frame_gray)
                contours_light, debug_thresh_light = self.find_bounding_box_light(frame_gray)

                ### find the center of frame ###
                center_x_light, center_y_light = self.calculate_center(contours_light)
                center_x_frame, center_y_frame = self.calculate_center(contours_frame)

                ### draw main center of target ###
                center_color_target = 0
                for idx, el in enumerate(center_x_light):
                    cv2.circle(frame, (center_x_light[idx], center_y_light[idx]), 14, (255, 0, center_color_target), -1)
                    center_color_target += 100

                ### draw main center of frame ###
                center_color_frame = 0
                for idx, el in enumerate(center_x_frame):
                    cv2.circle(frame, (center_x_frame[idx], center_y_frame[idx]), 14, (0, 255, center_color_frame), -1)
                    center_color_frame += 100

                ### draw bounding box of target ###
                area_color_target = 0
                for cnt in contours_light:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 10)
                    area_color_target += 100

                ### draw bounding box of frame ###
                area_color_bounding_box_frame = 0
                for cnt in contours_frame:
                    x, y, w, h = cv2.boundingRect(cnt)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, area_color_bounding_box_frame), 10)
                    area_color_bounding_box_frame += 100

                ### warp all draw in same image frame ### 
                frame_with_contours = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                ### convert frame to kivy texture ###
                buffer = frame_with_contours.tobytes()
                convert_frame_to_kivy = Texture.create(size=(frame_with_contours.shape[1], frame_with_contours.shape[0]), colorfmt='rgb')
                convert_frame_to_kivy.blit_buffer(buffer, colorfmt='rgb', bufferfmt='ubyte')

                ### send frame to frontend ###
                self.ids.auto_cam_image.texture = convert_frame_to_kivy
                self.ids.auto_center_target_position.text = "X: " + str(center_x_light[0]) + "px" + " Y: " + str(center_y_light[0]) + "px"
                self.ids.auto_center_frame_position.text = "X: " + str(center_x_frame[0]) + "px" + " Y: " + str(center_y_frame[0]) + "px"
                self.ids.auto_bounding_frame_position.text = "X: " + str(x) + "px Y: " + str(y) + "px W: " + str(w) + "px H: " + str(h) + "px"
                self.ids.auto_error_center.text = "X: " + str(center_x_frame[0] - center_x_light[0]) + "px Y: " + str(center_y_frame[0] - center_y_light[0]) + "px"

    def call_close_camera(self):
        if self.capture:
            self.capture.release()
            self.capture = None
            Clock.unschedule(self.update_frame)
            self.ids.camera_status.text = "Auto menu || camera status off"

class SettingScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.on_fetch_data()

    def on_fetch_data(self):
        # self.ids.list_helio_stats_ip.data = [{'text': item} for item in ["item1", "item2", "item3"]]
        # print(self.ids.list_helio_stats_ip)
        # try:
        #     with open('./data/setting/setting.json', 'r') as file:
        #         data = json.load(file)
        #         # Process the data into the format expected by RecycleView
        #         self.helio_stats_data = [{'text': str(item)} for item in data.get('helio_stats_ip', [])]
        #         print(self.helio_stats_data)
        # except (FileNotFoundError, json.JSONDecodeError) as e:
        #     print(f"Error loading JSON data: {e}")
        #     self.helio_stats_data = []  
            
    def func_adding_array_helio_stats(self):
        pass
    def func_adding_camera_array_ip(self):
        pass

    def haddle_submit_url(self):
        helio_stats_input_id = self.ids.helio_stat_input.text
        url_ip_input = self.ids.ipv4_input.text
        url_cam_input = self.ids.ip_cam_input.text
        self.ids.display_helio_stats_id.text = f'Helio stats ID:: {helio_stats_input_id}'
        self.ids.display_ipv4.text = f'IPv4: {url_ip_input}'
        self.ids.display_cam_text.text = f'Camera Url :{url_cam_input}'


class LabHeaderWidget(BoxLayout):
    pass

class MainFrameWidget(BoxLayout):
    pass

class SolarControlApp(App):
    pass

if __name__ == "__main__":
    SolarControlApp().run()
