import requests
from datetime import datetime
import json
class ControlHelioStats():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    

    def haddle_check_ip(self):
        pass
    ### handle path heliostats ### 
    def find_nearest_time_and_send(self, list_path_data, ip):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        headers = {
            'Content-Type': 'application/json'  
        }
        nearest = min(list_path_data, key=lambda entry: abs(datetime.strptime(entry["timestamp"], "%H:%M:%S") - current_time))
        try:
            result =  requests.post("http://"+ip, data=json.dumps(nearest), headers=headers, timeout=5)
            if result.status_code != 200:
                return {"is_fail":True}
            else:
                return {"is_fail": False}
        except Exception as e:
            return {"is_fail": True}


    def move_left(self):
        pass

    def move_right(self):
        pass

    def move_down(self):
        pass

    def move_up(self):
        pass

    def stop_move(self, id, ip):
        payload_set = {"topic":"stop"}
        try:
            response = requests.post("http://"+ip+"/update-data", json=payload_set, timeout=5)
            if response.status_code == 200:
                pass
            else:
                self.show_popup("Error", f"Connecton error status code {str(response.status_code)}")
        except Exception as e:
            self.show_popup("Error", f"Connecton error {str(e)}")
