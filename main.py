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

from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen

### from kivy.core.window import Window ### windows fix 
from kivy.uix.textinput import TextInput
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
import requests
import time
import numpy as np



class GUIControlToolsWidge(GridLayout):
    def push_upper(self):
        print("Upper")

    def push_left(self):
        print("Left")

    def push_down(self):
        print("Down")

    def push_right(self):
        print("Right")


class ManualScreen(Screen):
    pass

class SetAutoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.parent_screen = parent_screen 
        self.capture = None

    def call_open_camera(self):
        if not self.capture:
            self.capture = cv2.VideoCapture(0)
            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
            self.ids.auto_lable_mode.text = "Auto on"

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

    def update_frame(self,dt):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                ### variable waiting to update ###
                x_center_light = 0
                y_center_light = 0
                x_center_frame = 0
                y_center_frame = 0
                
                bounding_box_frame_x = 0
                bounding_box_frame_y = 0
                bounding_box_frame_w = 0
                bounding_box_frame_h = 0

                ### open camera system ###
                image = cv2.imread('/Users/pcsishun/project_solar_thermal/gui_solar_control/test10.png')
                frame = cv2.flip(image, 0) # flip frame
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # convert to grayscale
                
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
                self.ids.cam_image.texture = convert_frame_to_kivy
                self.ids.auto_center_target_position.text = "X: " + str(center_x_light[0])+"px"+ " " + "Y: " + str(center_y_light[0])+"px" ### light center target must have 1 center
                self.ids.auto_center_frame_position.text =  "X: "+  str(center_x_frame[0])+"px"+ " " + "Y: " + str(center_y_frame[0])+"px" ### frame center target must have 1 center
                self.ids.auto_bounding_frame_position.text =  "X: " + str(bounding_box_frame_x)+"px" + " " + "Y: " + str(bounding_box_frame_y)+"px" + " " + "W: " + str(bounding_box_frame_w)+"px" + " " + "H: " + str(bounding_box_frame_h)+"px"
                self.ids.auto_error_center.text = "X: " + str(x_center_frame - x_center_light)+"px" + " " + "Y: " + str(y_center_frame - y_center_light) + "px"

    def call_close_camera(self):
        print("btn off")
        if self.capture:
            print("off")
            self.capture.release()
            self.capture = None
            Clock.unschedule(self.update_frame)
            self.ids.auto_lable_mode.text = "Auto off"


class SettingScreen(Screen):
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
    # def build(self):

    #     return sm

if __name__ == "__main__":
    SolarControlApp().run()
