import json
from kivy.uix.recycleview import RecycleView

class ListCameraIp(RecycleView):
    def __init__(self, **kwargs):
        super(ListCameraIp, self).__init__(**kwargs)
        with open('./data/setting/connection.json', 'r') as file:
            json_data = json.load(file)
            self.data = [{'text': item} for item in  json_data.get('camera_url',[])]