from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
# from threading import Thread
# from flask import Flask, request
# import json 

# flask_api = Flask(__name__)

# API_TYPE = ["h-callback", "origin-callback"]

# @flask_api.route('/callback', methods=['POST']) 
# def get_status_return_esp():
#     data = request.get_json()
#     print(data)
#     update_esp_call_back(status_in=data['status'], api_type=API_TYPE[0])
#     return "ok"
# @flask_api.route('/origin-callback', methods=['POST'])
# def get_status_origin_callback():
#     data = request.get_json()
#     print(data)
#     update_esp_call_back(status_in=data['status'], api_type=API_TYPE[1])
#     return "ok"
    
# def update_esp_call_back(status_in, api_type):
#     if  API_TYPE[0] == api_type:
#         try:
#             with open("./data/setting/status_return.json", 'r') as file:
#                 storage = json.load(file)
#                 storage['esp_status_call_back'] = status_in
#             with open("./data/setting/status_return.json", 'w') as file_change:
#                 json.dump(storage, file_change)
#         except Exception as e:
#             print("error save status in to status_return.json!")
#     else:
#         try:
#             with open("./data/setting/status_return.json", 'r') as file:
#                 storage = json.load(file)
#                 storage['esp_origin_call_back'] = status_in
#             with open("./data/setting/status_return.json", 'w') as file_change:
#                 json.dump(storage, file_change)
#         except Exception as e:
#             print("error save status in to status_return.json!")

# def run_flask():
#     flask_api.run(host='0.0.0.0', port=8891, debug=False, use_reloader=False)

class LabHeaderWidget(BoxLayout):
    def change_screen(self, screen_name, text):
        screen_manager = self.ids.screen_manager
        self.ids.screen_manager.current = screen_name
        app = App.get_running_app()
        app.current_mode = text
        current_screen = screen_manager.current_screen
        current_screen.call_close_camera()
        current_screen.haddle_off_get_data()
        current_screen.stop_fetch_loop()

class MainFrameWidget(BoxLayout):
    pass

class SolarControlApp(App):
    current_mode = StringProperty('')

if __name__ == '__main__':
    # Start Flask in a separate thread
    # flask_thread = Thread(target=run_flask, daemon=True)
    # flask_thread.start()
    SolarControlApp().run()