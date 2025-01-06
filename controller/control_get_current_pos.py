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
        try:
            # list_url = CrudData.open_list_connection()
            standby_json = CrudData.read_standby()
            pending_json = CrudData.read_pending()
            fail_conn_json = CrudData.read_fail_conn()

            for url in list_url:
                try:
                    result = requests.get("http://" + url, timeout=3)
                    setJson = result.json()

                    if result.status_code == 200:
                        payload = {
                            "url": url,
                            "current_x": setJson['currentX'],
                            "current_y": setJson['currentY']
                        }
                        standby_json.append(payload)
                        # CrudData.read_standby(payload)
                        self.standby_url.append(payload)
                    else:
                        payload = {"url": url}
                        pending_json.append(payload)
                        # CrudData.read_pending(payload)
                        self.pending_url.append(payload)
                except Exception as req_error:
                    print(f"Error connecting to {url}: {req_error}")
                    pending_json.append({"url": url})
            
            if len(self.pending_url) > 0:
                for url in self.pending_url:
                    try:
                        result = requests.get("http://" + url, timeout=3)
                        setJson = result.json()
                        if result.status_code == 200:
                            payload = {
                                "url": url,
                                "current_x": setJson['currentX'],
                                "current_y": setJson['currentY']
                            }
                            standby_json.append(payload)
                            self.pending_url.remove(url)
                            pending_json.remove(url)
                            self.standby_url.append(payload)

                            with open("./data/standby_conn/pending.json", 'w') as update_pending_file:
                                json.dump(pending_json, update_pending_file)
                        else:
                            payload = {"url": url}
                            fail_conn_json.append(payload)
                            # CrudData.save_fail_conn(payload)
                            self.fail_url.append(payload)
                    except Exception as req_error:
                        print(f"Error connecting to {url}: {req_error}")
                        payload = {"url": url}
                        fail_conn_json.append(payload)
                        # CrudData.save_fail_conn(payload)
                        self.fail_url.append(payload)

            CrudData.update_standby(standby_json)
            CrudData.update_pending(pending_json)
            CrudData.update_failconn(fail_conn_json)
            return self.standby_url, self.pending_url, self.fail_url
        except Exception as e:
            print(f"Error in handler_get_current_pos: {e}")