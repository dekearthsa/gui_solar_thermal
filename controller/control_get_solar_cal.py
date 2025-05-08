import math
from datetime import datetime
import pytz
class ControlCalSolar():
    def __init__(self, **kwargs):
        
        super().__init__(**kwargs)
    
    def get_solar_declination(self, date: datetime):
        ## day_of_year 1 for January 1 to 365 for December 31
        
        day_of_year = date.timetuple().tm_yday
        ## 23.44 is the Earth's axial tilt.
        declination = -23.44 * math.cos(math.radians(360/365) * (day_of_year + 10))
        return declination
    
    def get_solar_hour_angle(self,date:datetime, longitude: float):
        day_of_year = date.timetuple().tm_yday
        B = math.radians((360 / 365) * (day_of_year - 81))
        EOT = 9.87 * math.sin(2 * B) - 7.53 * math.cos(B) - 1.5 * math.sin(B)
        # Convert current time to UTC
        utc_time = date.astimezone(pytz.utc)
        utc_hour = utc_time.hour + utc_time.minute / 60 + utc_time.second / 3600

        # Local Solar Time (LST)
        LST = utc_hour + (longitude / 15) + (EOT / 60)

        # Solar Hour Angle (H)
        hour_angle = 15 * (LST - 12)  # 15° per hour
        return hour_angle