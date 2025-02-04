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
        # print("find_nearest_time_and_send => " + ip)
        # print(list_path_data)
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        # print("current_time => ", current_time)
        headers = {
            'Content-Type': 'application/json'  
        }
        current_time_as_datetime = datetime.strptime(current_time, "%H:%M:%S")
        nearest = min(list_path_data, key=lambda entry: abs(datetime.strptime(entry["timestamp"], "%H:%M:%S") - current_time_as_datetime))
        print("nearest => ", nearest)
        try:
            ### Endpoint for send path data?? ### 
            result =  requests.post("http://"+ip+"/update-data", data=json.dumps(nearest), headers=headers, timeout=5)
            if result.status_code != 200:
                return {"is_fail":True}
            else:
                return {"is_fail": False}
        except Exception as e:
            return {"is_fail": True}

    def fine_tune_heliostats(self):
        pass

    def move_left(self):
        pass

    def move_right(self):
        pass

    def move_down(self):
        pass

    def move_up(self):
        
        pass

    ## function move back (pos right) ##
    def move_helio_in(self, ip):
        payload_set = {
            "topic":"forward",
            "step": 100,
            "speed": 500,
        }
        try:
            response = requests.post("http://"+ip+"/update-data", json=payload_set, timeout=10)
            if response.status_code == 200:
                return {"is_fail":False}
            else:
                return  {"is_fail":True}
        except Exception as e:
            print("Error move_helio_in => " + f"{e}")
            return  {"is_fail":True}
    
    ## function move out (pos left) ##
    def move_helio_out(self, ip):
        payload_set = {
            "topic":"reverse",
            "step": 100,
            "speed": 500,
        }
        try:
            response = requests.post("http://"+ip+"/update-data", json=payload_set, timeout=10)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            print("Error move_helio_out => " + f"{e}")
            return False

    def stop_move(self, ip):
        
        payload_set = {"topic":"stop"}
        try:
            response = requests.post("http://"+ip+"/update-data", json=payload_set, timeout=5)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            print("Error connection " + f"{e}")
            return False
