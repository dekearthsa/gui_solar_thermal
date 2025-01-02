import json


class CrudData:
    def __init__(
            self,
            path_standby_json="./data/setting/standby.json",
            path_pending_json="./data/setting/pending.json",
            path_fail_json="./data/setting/failconn.json",
            path_setting_json="./data/setting/setting.json",
            path_connection_json="./data/setting/connection.json",
            path_origin_json="./data/standby_conn/origin_fail.json"
    ):
        self.path_standby_json = path_standby_json
        self.path_pending_json = path_pending_json
        self.path_fail_json = path_fail_json
        self.path_setting_json = path_setting_json
        self.path_connection_json = path_connection_json
        self.path_origin_json = path_origin_json

    def open_list_connection(self):
        print("open list helio stats conn...")
        try:
            with open('./data/setting/connection.json', 'r') as file:
                storage = json.load(file)
                list_conn = storage['helio_stats_ip']
                return list_conn
        except Exception as e:
            print("Error ")

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

    def save_standby(self, url):
        print("save ip helio stats....")
        try:
            with open('./data/standby_conn/standby.json', 'r') as file:
                list_standby = json.load(file)
                list_standby.append(url)
            with open('./data/standby_conn/standby.json', 'w') as file_save:
                json.dump(list_standby, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save standby: {e}")
        print("done save ip helio stats.")

    def save_fail_conn(self, url):
        print("save ip helio stats....")
        try:
            with open('./data/standby_conn/failconn.json', 'r') as file:
                list_failconn = json.load(file)
                list_failconn.append(url)
            with open('./data/standby_conn/failconn.json', 'w') as file_save:
                json.dump(list_failconn, file_save)
        except Exception as e:
            self.show_popup("Error", f"Failed to save failconn: {e}")
        print("done save ip helio stats.")

    def remove_by_id_pending(self, url):
        print("remove pending...")
        try:
            with open('./data/standby_conn/pending.json', 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != url['url']]

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

    def read_fail_origin(self):
        print("read origin...")
        try:
            with open(self.path_origin_json, 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            print("Error read_fail_origin " + f"{e}")
        print("read finish.")

    def save_origin(self, payload):
        print("Save origin is fail.")
        try:
            with open(self.path_origin_json, 'w') as file:
                json.dump(payload, file)
        except Exception as e:
            print("Error save_origin" + f"{e}")
        print("Finish origin is fail.")

    def update_origin(self, payload):
        print("update origin...")
        try:
            with open(self.path_origin_json, 'w') as file:
                json.dump(payload, file, indent=4)
        except Exception as e:
            print("Error open file failconn " + f"{e}")
        print("update finish")

    def remove_by_id_origin(self, payload):
        print("remove origin by id...")
        try:
            with open(self.path_origin_json, 'r') as file:
                data=json.load(file)
            data = [item for item in data if item.get("url") != payload['url']]

            with open(self.path_origin_json, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            print("error read failconn.json file" + f"{e}") 
        print("remove finish.")