from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import cv2
# import requests
# import time


class AutoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.parent_screen = parent_screen 
        self.capture = None

    def open_camera(self):
        if not self.capture:
            self.capture = cv2.VideoCapture(0)
            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)  # 30 FPS
            self.parent_screen.ids.auto_lable_mode.text = "Auto on"

    def update_frame(self):
        if self.capture:
            ret, frame = self.capture.read()
            if ret:
                image = cv2.imread('/Users/pcsishun/project_solar_thermal/gui_solar_control/test.png')
                frame = cv2.flip(image, 0)
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(frame_gray, 127, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
                frame_with_contours = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                buffer = frame_with_contours.tobytes()
                texture = Texture.create(size=(frame_with_contours.shape[1], frame_with_contours.shape[0]), colorfmt='rgb')
                texture.blit_buffer(buffer, colorfmt='rgb', bufferfmt='ubyte')
                self.parent_screen.ids.cam_image.texture = texture

    def stop_camera(self):
        print("btn off")
        if self.capture:
            print("off")
            self.capture.release()
            self.capture = None
            Clock.unschedule(self.update_frame)
            self.parent_screen.ids.auto_lable_mode.text = "Auto off"

    # def get_data_from_server(self):
    #     try:
    #         response = requests.get('http://localhost:2222/get')
    #         # print("response => ", response)
    #         json_d = response.json()
    #         # print("data => ",json_d)
    #         self.update_label_with_data(json_d['data'])
    #     except requests.RequestException as e:
    #         self.update_label_with_data(str(e))

    # def update_label_with_data(self, data):
    #     self.counting += 1
    #     self.ids.data_label.text = data + "fetch count: " + str(self.counting)