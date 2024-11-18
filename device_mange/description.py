from kivy.uix.screenmanager import Screen
import json 
import requests
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.clock import Clock
from datetime import datetime
from kivy.app import App
class Description(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)  
        self.start_loop=False
        self.helio_endpoint=""
        self.status_auto_get="Auto get data off"
        Clock.schedule_once(lambda dt: self.fetch_helio_stats_list())
        self.menu_now="description"

    # def receive_text(self, text):
    #     app = App.get_running_app()
    #     current_mode = app.current_mode  # Assuming you have a global property 'current_mode'
    #     if self.menu_now != current_mode:
    #         self.stop_fetch_loop()
    #     else:
    #         self.checking_menu()

    # def checking_menu(self):
    #     Clock.schedule_interval(self.receive_text, 2)

    # def close_loop(self):
    #     Clock.unschedule(self.receive_text)

    def start_fetch_loop(self):
        if self.start_loop == False:
            self.start_loop = True
            self.status_auto_get = "Auto get data on"
            Clock.schedule_interval(self.haddle_fetch_loop, 2)
        else: 
            self.start_loop = False
            self.status_auto_get = "Auto get data off"
            self.stop_fetch_loop()

    def stop_fetch_loop(self):
        Clock.unschedule(self.haddle_fetch_loop)

    def haddle_fetch_loop(self):
        if self.self.helio_endpoint != "":
            try:
                data = requests.get(url="http://"+self.helio_endpoint)
                set_data = json.load(data)
                now = datetime.now()
                timestamp = now.strftime("%d/%m/%y %H:%M:%S")

                self.ids.d_timestamp.text = timestamp
                self.ids.d_currentX.text = str(set_data['currentX'])
                self.ids.d_currentY.text = str(set_data['currentY'])
                self.ids.d_err_posx.text = str(set_data['err_posx'])
                self.ids.d_err_posy.text = str(set_data['err_posy'])
                self.ids.d_x.text = str(set_data['safety']['x'])
                self.ids.d_y.text = str(set_data['safety']['y'])
                self.ids.d_x1.text = str(set_data['safety']['x1'])
                self.ids.d_y1.text = str(set_data['safety']['y1'])
                self.ids.d_ls1.text = str(set_data['safety']['ls1'])
                self.ids.d_st_path.text = str(set_data['safety']['st_path'])
                self.ids.d_move_comp.text = str(set_data['safety']['move_comp'])
                self.ids.d_elevation.text = str(set_data['elevation'])
                self.ids.d_azimuth.text = str(set_data['azimuth'])
            except Exception as e:
                self.show_popup("Error", f"{e}")
        else:
            self.show_popup("Error", "Not found heliostats endpoint")

    def haddle_fetch_once(self):
        if self.start_loop == True:
            self.show_popup("Alert", "Auto get data is running.")
        else:
            if self.self.helio_endpoint != "":
                try:
                    data = requests.get(url="http://"+self.helio_endpoint)
                    set_data = json.load(data)
                    now = datetime.now()
                    timestamp = now.strftime("%d/%m/%y %H:%M:%S")

                    self.ids.d_timestamp.text = timestamp
                    self.ids.d_currentX.text = str(set_data['currentX'])
                    self.ids.d_currentY.text = str(set_data['currentY'])
                    self.ids.d_err_posx.text = str(set_data['err_posx'])
                    self.ids.d_err_posy.text = str(set_data['err_posy'])
                    self.ids.d_x.text = str(set_data['safety']['x'])
                    self.ids.d_y.text = str(set_data['safety']['y'])
                    self.ids.d_x1.text = str(set_data['safety']['x1'])
                    self.ids.d_y1.text = str(set_data['safety']['y1'])
                    self.ids.d_ls1.text = str(set_data['safety']['ls1'])
                    self.ids.d_st_path.text = str(set_data['safety']['st_path'])
                    self.ids.d_move_comp.text = str(set_data['safety']['move_comp'])
                    self.ids.d_elevation.text = str(set_data['elevation'])
                    self.ids.d_azimuth.text = str(set_data['azimuth'])
                except Exception as e:
                    self.show_popup("Error", f"{e}")
            else:
                self.show_popup("Error", "Not found heliostats endpoint")

    def fetch_helio_stats_list(self):
        with open('./data/setting/connection.json', 'r') as file:
            data = json.load(file)
        self.ids.spinner_helio_stats_desc.values  = [item['id'] for item in data.get('helio_stats_ip', [])]

    def haddle_helio_stats_selection(self, spinner,text):
        
        try:
            with open('./data/setting/connection.json', 'r') as file:
                data = json.load(file)
            for helio_stats in data['helio_stats_ip']:
                if text == helio_stats['id']:
                    self.helio_endpoint = helio_stats['ip']
        except Exception as e:
            print("Error" , e)
            self.show_popup("Error", f"{e}")

    def show_popup(self, title, message):
        ###Display a popup with a given title and message.###
        popup = Popup(title=title,
                content=Label(text=message),
                size_hint=(None, None), size=(400, 200))
        popup.open()