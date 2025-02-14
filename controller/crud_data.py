
import json
from datetime import datetime, timedelta

class CrudData:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path_standby_json = "./data/setting/standby.json"
        self.path_pending_json = "./data/setting/pending.json"
        self.path_fail_json = "./data/setting/failconn.json"
        self.path_setting_json = "./data/setting/setting.json"
        self.path_connection_json = "./data/setting/connection.json"
        self.path_origin_json = "./data/standby_conn/origin_standby.json"
        self.path_current_pos = "./data/standby_conn/current_pos.json"
        self.path_receiver = "./data/receiver/result"
        self.path_calibrate = "./data/calibrate/result"
        # self.path_status_esp_call_back = "./data/setting/status_return.json"
        self.previous_date_lookback = 7

    def read_esp_call_back( status_in):
        try:
            with open("./data/setting/status_return.json", "r") as file:
                storage = json.load(file)
            return storage['esp_status_call_back']
        except Exception as e:
            print("error save status in to status_return.json!")

    def roll_back_esp_status(self):
        try:
            with open("./data/setting/status_return", "r") as file:
                storage = json.load(file)
                storage['esp_status_call_back'] = False
            with open("./data/setting/status_return", "w") as file_update:
                json.dump(storage,file_update)
        except Exception as e:
            print("Error roll_back_esp_status")

    def open_list_connection(self):
        
        print("open list helio stats conn...")
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
                list_conn = storage['helio_stats_ip']
                return list_conn
        except Exception as e:
            print("Error open_list_connection")
            # print("Error " + e)

    def read_curre(self):
        print("open read pending...")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read pending.json " + f"{e}")
        print("done read pending.")

    def read_pending(self):
        print("open read pending...")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read pending.json " + f"{e}")
        print("done read pending.")

    def read_fail_conn(self):
        print("open read fail_conn...")
        try:
            with open('./data/standby_conn/failconn.json', 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read failconn.json " + f"{e}")
        print("done read fail_conn.")

    def read_standby(self):
        print("open read standby...")
        try:
            with open('./data/standby_conn/standby.json', 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read standby.json " + f"{e}")
        print("done read standby.")

    def save_pending(self, url):
        
        print("save pending ip helio stats....")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                list_pending = json.load(file)
                list_pending.append(url)
            with open('./data/standby_conn/pending.json', 'w') as file_save:
                json.dump(list_pending, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save pending: {e}")
        print("done save pending ip helio stats.")

    def save_standby(self, payload):
        print("save ip helio stats....")
        try:
            with open('./data/standby_conn/standby.json', 'r') as file:
                list_standby = json.load(file)
                list_standby.append(payload)
            with open('./data/standby_conn/standby.json', 'w') as file_save:
                json.dump(list_standby, file_save)
        except Exception as e:
            print("Error" + f"Failed to save standby: {e}")
        print("done save ip helio stats.")

    def save_fail_conn(self, payload):
        print("save ip helio stats....")
        try:
            with open('./data/standby_conn/failconn.json', 'r') as file:
                list_failconn = json.load(file)
                list_failconn.append(payload)
            with open('./data/standby_conn/failconn.json', 'w') as file_save:
                json.dump(list_failconn, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save failconn: {e}")
        print("done save ip helio stats.")

    def remove_by_id_pending(self, payload):
        print("remove pending...")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != payload['url']]

            with open('./data/standby_conn/pending.json', 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read pending.json file" + f"{e}")

    def remove_by_id_standby(self, url):
        print("remove standby.json...")
        try:
            with open('./data/standby_conn/standby.json', 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != url['url']]

            with open('./data/standby_conn/standby.json', 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read standby.json file" + f"{e}")

    def remove_by_id_fail_conn(self, url):
        print("remove failconn.json...")
        try:
            with open('./data/standby_conn/failconn.json', 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != url['url']]

            with open('./data/standby_conn/failconn.json', 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read failconn.json file" + f"{e}")

    def update_current_pos(self,payload):
        print("update_current_pos...")
        try:
            with open("./data/standby_conn/current_pos.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file update_standby " + f"{e}")
        print("update_current_pos finish.") 

    def update_standby(self, payload):
        print("update stanby...")
        try:
            with open("./data/standby_conn/standby.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file update_standby " + f"{e}")
        print("update finish.") 

    def update_pending(self, payload):
        print("update pending...")
        try:
            with open("./data/standby_conn/pending.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file pending " + f"{e}")
        print("update finish.")

    def update_failconn(self, payload):
        print("update failconn...")
        try:
            with open("./data/standby_conn/failconn.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file failconn " + f"{e}")
        print("update finish.")

    def save_origin(self, payload):
        print("save success set origin...")
        try:
            with open("./data/standby_conn/origin_standby.json", 'w') as file:
                json.dump(payload, file)
        except Exception as e:
            print("Error save_origin" + f"{e}")
        print("save origin successed.")

    def read_fail_origin(self):
        
        print("read origin...")
        try:
            with open("./data/standby_conn/origin_fail.json", 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read_fail_origin " + f"{e}")
        print("read finish.")

    def save_fail_origin(self, payload):
        print("Save origin is fail.")
        try:
            with open("./data/standby_conn/origin_fail.json", 'w') as file:
                json.dump(payload, file)
        except Exception as e:
            print("Error save_origin" + f"{e}")
        print("Finish origin is fail.")

    def update_origin(self, payload):
        print("update origin...")
        try:
            with open("./data/standby_conn/origin_fail.json", 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file failconn " + f"{e}")
        print("update finish")

    def remove_by_id_origin(self, payload):
        print("remove origin by id...")
        try:
            with open("./data/standby_conn/origin_fail.json", 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != payload['url']]

            with open("./data/standby_conn/origin_fail.json", 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read failconn.json file" + f"{e}") 
        print("remove finish.")

    def convert_id_to_ip(self, id):
        list_ip = self.open_list_connection()
        for data_id in list_ip:
            if id == data_id['id']:
                return data_id['ip']
            
    def convert_ip_to_id(self, ip):
        list_id = self.open_list_connection()
        for data_id in list_id:
            if ip == data_id['ip']:
                return data_id['id']

    def open_previous_data(self, target, heliostats_id):
            print("Start open_previous_data func...")
            # print("open_previous_data => ",target, heliostats_id)
            # print("self.path_calibrate => ", self.path_calibrate)
            # print("self.previous_date_lookback => ", self.previous_date_lookback)
            data_list = []
            # file_not_found = []
            counting_date = 0
            now = datetime.now()
            if target == "camera-bottom": ## calibrate
                for is_date in range(7):
                    counting_date += 1
                    previous_date = now - timedelta(days=is_date + 1)
                    path_time_stamp = previous_date.strftime("%d_%m_%y"+"_"+heliostats_id)
                    print(path_time_stamp)
                    try:
                        with open("./data/calibrate/result"+"/"+path_time_stamp+"/data.txt" , 'r') as file:
                            # print("file => ",file)
                            for line in file:
                                clean_line = line.lstrip('*').strip()
                                data_list.append(json.loads(clean_line))
                        break
                    except Exception as e:
                        # file_not_found.append()
                        print("cannot find " + "../data/calibrate/result"+"/"+path_time_stamp+"/data.txt " + "find previous date..." + str(e))
                
                if  counting_date >= 7:
                    print("cannot find date")
                    return {'found': False, 'data':[]}
                else:
                    return {'found': True ,'data':data_list}
            else: ## receiver
                for is_date in range(7):
                    # print("is_date => ",is_date)
                    counting_date += 1
                    previous_date = now - timedelta(days=is_date + 1)
                    # print(previous_date)
                    path_time_stamp = previous_date.strftime("%d_%m_%y"+"_"+heliostats_id)
                    print(path_time_stamp)
                    try:
                        with open("./data/receiver/result"+"/"+path_time_stamp+"/data.txt" , 'r') as file:
                            # print("file => ",file)
                            for line in file:
                                clean_line = line.lstrip('*').strip()
                                data_list.append(json.loads(clean_line))
                        break
                    except Exception as e:
                        print("cannot find " + "../data/receiver/result"+"/"+path_time_stamp+"/data.txt " + "find previous date..." + str(e))
                
                if  counting_date >= 7:
                    print("cannot find date")
                    return {'found': False, 'data':[]}
                else:
                    return {'found': True ,'data':data_list}