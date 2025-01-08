import requests
from controller.crud_data import CrudData

class ControlCheckConnHelioStats():

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_loop_update = 5 ## 2 sec test update frame
        self.standby_url =[]
        self.fail_url = []
        self.pending_url = []

    def handler_checking_connection(self, list_conn):  ## data from connection.json {}
        print("checking connection helio stats....")
        print("list_conn => ", list_conn)
        i=0
        for el in list_conn:
            if el['ip'] != 'all':
                while i < self.time_loop_update:
                    result = requests.get(url="http://"+el['ip'], timeout=3)
                    payload = {
                        "id": el['id'],
                        "ip": el['ip']
                    }
                    if result.status_code == 200:
                        CrudData.save_standby(self,payload=payload)
                        self.standby_url.append(payload)
                        break
                    else:
                        i += 1
                        if i >= self.time_loop_update:
                            CrudData.save_pending(self,payload=payload)
                            self.pending_url.append(payload)
        if len(self.pending_url) > 0:
            self.handler_reconn_pending()
            print("checking connection helio stats done!")
            return self.standby_url, self.pending_url, self.fail_url
        else:
            print("checking connection helio stats done!")
            return self.standby_url, self.pending_url, self.fail_url

    def handler_reconn_pending(self):
        print("checking reconnect pending...")
        for data in self.pending_url:
            result = requests.get(url="http://"+data['ip'], timeout=3)
            payload = {
                "id": data['id'],
                "ip": data['ip']
            }
            if result.status_code == 200:
                self.standby_url.append(payload)
            else:
                self.fail_url.append(payload)
        self.pending_url = []
        print("done checking reconnect pending.")