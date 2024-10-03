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

from camera_control.auto_screen_widget import AutoScreen


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

# class SetAutoScreen(Screen):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.auto_screen = AutoScreen(parent_screen=self) 
#         # self.add_widget(auto_screen)

#     def call_open_camera(self):
#         self.auto_screen.open_camera()

#     def call_close_camera(self):
#         self.auto_screen.stop_camera()

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
                image = cv2.imread('/Users/pcsishun/project_solar_thermal/gui_solar_control/test4.png')
                frame = cv2.flip(image, 0)
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(frame_gray, 0, 255, cv2.THRESH_BINARY)

                contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)                
                center_x, center_y = self.calculate_center(contours)
                # print("center_x => ",  center_x)
                # print("center_y => ", center_y)

                cnt = contours[0]
                area = cv2.contourArea(cnt)
                perimeter = cv2.arcLength(cnt,True)
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
    
                x,y,w,h = cv2.boundingRect(cnt)
                
                center_color = 0
                for idx,el in  enumerate(center_x):
                    ### draw main center of target ###
                    center_color += 50
                    cv2.circle(frame, (center_x[idx], center_y[idx]), 30,(0,255,center_color),-1 )
                    
                center_color = 0
                for cnt in contours:
                    center_color += 50
                    x,y,w,h = cv2.boundingRect(cnt)
                    cv2.putText(frame, "X:"+str(x) + " " + "Y:"+str(y) +" "+ "W:"+str(w) +" "+ "H:"+str(h),(x,h-120), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,center_color), 10)

                ### draw borunding box of image frame ###
                cv2.drawContours(frame, contours, 0, (255, 0, 0), 3)
                ### draw main target box of image frame ###
                cv2.drawContours(frame,[box],0,(50,40,255),3)
                # print("box => ", box[0][0])
                


                ### warp all draw in same image frame ### 
                frame_with_contours = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                buffer = frame_with_contours.tobytes()
                thresh = Texture.create(size=(frame_with_contours.shape[1], frame_with_contours.shape[0]), colorfmt='rgb')
                thresh.blit_buffer(buffer, colorfmt='rgb', bufferfmt='ubyte') # luminance
                self.ids.cam_image.texture = thresh

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
