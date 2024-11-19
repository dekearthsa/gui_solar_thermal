import json
from kivy.uix.recycleview import RecycleView


class ListHelioStatsIp(RecycleView):
    def __init__(self, **kwargs):
        super(ListHelioStatsIp, self).__init__(**kwargs)
        self.load_data()

    def load_data(self):
        try:
            with open('./data/setting/connection.json', 'r') as file:
                json_data = json.load(file)
            self.data = [{'text': str(item)} for item in json_data.get('helio_stats_ip', [])]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading Helio Stats IPs: {e}")
            self.data = [{'text': 'Error loading data'}]

    def reload(self):
        self.load_data()