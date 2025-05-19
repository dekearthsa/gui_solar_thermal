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
        nearest['topic'] = 'mtt'
        try:
            ### Endpoint for send path data?? ### 
            result =  requests.post("http://"+ip+"/update-data", data=json.dumps(nearest), headers=headers, timeout=5)
            if result.status_code != 200:
                return {"is_fail":True}
            else:
                return {"is_fail": False}
        except Exception as e:
            return {"is_fail": True}

    ## function move back (pos right) ##
    def move_helio_in(self, target, heliostats_id,ip):
        print("move in process")
        data_list = []
        now = datetime.now()
        path_time_stamp = now.strftime("%d_%m_%y"+"_"+heliostats_id)
        if target == "camera-bottom":
            try:
                with open("./data/calibrate/result"+"/"+path_time_stamp+"/data.txt" , 'r') as file:
                    for line in file:
                        clean_line = line.lstrip('*').strip()
                        data_list.append(json.loads(clean_line))
            except Exception as e:
                print(e)
                return {"is_fail": True}
            return {"is_fail": False, "path":data_list}
            # return self.find_nearest_time_and_send(list_path_data=data_list,ip=ip)
            
        else:
            print("\npath_time_stamp = ",path_time_stamp)
            try:
                with open("./data/receiver/result"+"/"+path_time_stamp+"/data.txt" , 'r') as file:
                    for line in file:
                        clean_line = line.lstrip('*').strip()
                        print(clean_line)
                        data_list.append(json.loads(clean_line))
            except Exception as e:
                print(e)
                return {"is_fail": True}
            print("path ",data_list)
            # self.find_nearest_time_and_send(list_path_data=data_list,ip=ip )
            return {"is_fail": False, "path":data_list}
            # return self.find_nearest_time_and_send(list_path_data=data_list,ip=ip)
    

    ## function move out (pos left) ##
    def move_helio_out(self, ip ,payload ):
        ## example data payload ##
        # payload_set = {
        #     "topic":"mtt",
        #     "speed": 600,
        #     "x": 300.0,
        #     "y": 300.0,
        # }
        try:
            response = requests.post("http://"+ip+"/update-data", json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            print("Error move_helio_out => " + f"{e}")
            return False


    def stop_move(self, ip):
        
        
        payload_set = {"topic":"stop"}
        print("stop_move => ", ip)
        try:
            response = requests.post("http://"+ip+"/update-data", json=payload_set, timeout=5)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            print("Error connection " + f"{e}")
            return False
