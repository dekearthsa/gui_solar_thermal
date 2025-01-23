import requests
from controller.crud_data import CrudData
import json
class ControlGetCurrentPOS():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.standby_url = []
        self.pending_url = []
        self.fail_url = []
    
    def handler_get_current_pos(self, list_url):
        print("Start handler_get_current_pos....")
        print("list_url => ", list_url)
        try:
            # list_url = CrudData.open_list_connection()
            standby_json = CrudData.read_standby(self)
            pending_json = CrudData.read_pending(self)
            fail_conn_json = CrudData.read_fail_conn(self)

            for data in list_url:
                if data['ip'] != 'all':
                    try:
                        result = requests.get("http://" + data['ip'], timeout=3)
                        setJson = result.json()

                        if result.status_code == 200:
                            payload = {
                                "id": data['id'],
                                "ip": data['ip'],
                                "current_x": setJson['currentX'],
                                "current_y": setJson['currentY']
                            }
                            standby_json.append(payload)
                            # CrudData.read_standby(payload)
                            self.standby_url.append(payload)
                        else:
                            payload = {"ip": data['ip'], 'id':data['id']}
                            pending_json.append(payload)
                            # CrudData.read_pending(payload)
                            self.pending_url.append(payload)
                    except Exception as req_error:
                        print(f"Error connecting to {data}: {req_error}")
                        pending_json.append(data)
                        self.pending_url.append(data)

            if len(self.pending_url) > 0:
                for data in self.pending_url:
                    if data['ip'] != 'all':
                        try:
                            result = requests.get("http://" + data['ip'], timeout=3)
                            setJson = result.json()
                            if result.status_code == 200:
                                payload = {
                                    "id": data['id'],
                                    "ip": data['ip'],
                                    "current_x": setJson['currentX'],
                                    "current_y": setJson['currentY']
                                }
                                standby_json.append(payload)
                                self.pending_url.remove(data['ip'])
                                pending_json.remove(data['ip'])
                                self.standby_url.append(payload)

                                with open("./data/standby_conn/pending.json", 'w') as update_pending_file:
                                    json.dump(pending_json, update_pending_file)
                            else:
                                payload = {"ip": data['ip'], 'id':data['id']}
                                fail_conn_json.append(payload)
                                # CrudData.save_fail_conn(payload)
                                self.fail_url.append(payload)
                        except Exception as req_error:
                            print(f"Error connecting to {data}: {req_error}")
                            payload = {"ip": data['ip'], 'id':data['id']}
                            fail_conn_json.append(payload)
                            # CrudData.save_fail_conn(payload)
                            self.fail_url.append(payload)

            # print("standby_json => ",standby_json)
            CrudData.update_standby(self,payload=standby_json)
            CrudData.update_pending(self,payload=pending_json)
            CrudData.update_failconn(self,payload=fail_conn_json)
            # print("self.standby_url => ", self.standby_url)
            # print("self.pending_url => ", self.pending_url)
            # print("self.fail_url => ",self.fail_url)
            return self.standby_url, self.pending_url, self.fail_url
        
        except Exception as e:
            print(f"Error in handler_get_current_pos: {e}")