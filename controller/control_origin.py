import requests


class ControlOrigin():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_origin_x={"topic": "origin", "axis": "x", "speed":400}
        self.default_origin_y={"topic": "origin", "axis": "y", "speed":400}
        self.set_timeout=30
    def send_set_origin_x(self, ip, id):
        try:
            result_x = requests.post("http://"+ip+"/update-data", json=self.default_origin_x, timeout= self.set_timeout)
            if result_x.status_code != 200:
                print("Cannot set origin x"+ ip + " check connection" + e)
                return {"is_fail": True, "id":id,"ip": ip,"origin": "x"}
            else: 
                return {"is_fail": False,}
        except Exception as e:
            print("Cannot set origin x"+ ip + " check connection" + e)
            return  {"is_fail": True,"id":id,"ip": ip,"origin": "x"}

    def send_set_origin_y(self, ip):
        try:
            result_x = requests.post("http://"+ip+"/update-data", json=self.default_origin_y, timeout= self.set_timeout)
            if result_x.status_code != 200:
                print("Cannot set origin x"+ ip + " check connection" + e)
                return  {"is_fail": True,"id":id,"ip": ip,"origin": "y"}
            else: 
                return {"is_fail": False,}
        except Exception as e:
            print("Cannot set origin x"+ ip + " check connection" + e)
            return {"is_fail": True,"id":id,"ip": ip,"origin": "y"}