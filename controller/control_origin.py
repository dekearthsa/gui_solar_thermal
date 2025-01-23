import requests

class ControlOrigin():
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def send_set_origin_x(self, ip, id):
        print("send_set_origin_x => ", ip, id)
        payload = {"topic": "origin", "axis": "x", "speed":400}
        set_timeout = 30
        try:
            result_x = requests.post("http://"+ip+"/update-data", json=payload, timeout=set_timeout)
            if result_x.status_code != 200:
                print("Cannot set origin x"+ ip + " check connection" + str(e))
                return {"is_fail": True, "id":id,"ip": ip,"origin": "x"}
            else: 
                return {"is_fail": False,}
        except Exception as e:
            print("Cannot set origin x"+ ip + " check connection" +  str(e))
            return  {"is_fail": True,"id":id,"ip": ip,"origin": "x"}

    def send_set_origin_y(self, ip, id):
        print("send_set_origin_ => ", ip, id)
        payload = {"topic": "origin", "axis": "y", "speed":400}
        set_timeout = 30
        try:
            result_x = requests.post("http://"+ip+"/update-data", json=payload, timeout=set_timeout)
            if result_x.status_code != 200:
                print("Cannot set origin x"+ ip + " check connection" +  str(e))
                return  {"is_fail": True,"id":id,"ip": ip,"origin": "y"}
            else: 
                return {"is_fail": False,}
        except Exception as e:
            print("Cannot set origin x"+ ip + " check connection" +  str(e))
            return {"is_fail": True,"id":id,"ip": ip,"origin": "y"}