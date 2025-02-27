import datetime
import pytz
from pysolar.solar import get_altitude, get_azimuth, get_solar_declination, get_solar_hour_angle
from pysolar.radiation import get_radiation_direct

# Define the location (latitude, longitude)
latitude = 14.382198  # Example: Bangkok, Thailand
longitude = 100.842897

# Define the time (UTC)
tz = pytz.timezone("Asia/Bangkok")  # Set timezone
time = datetime.datetime.now(tz)  # Get current local time
time_utc = time.astimezone(pytz.utc)  # Convert to UTC

# Get solar altitude (elevation angle)
altitude = get_altitude(latitude, longitude, time_utc)

# Get solar azimuth (direction from North)
azimuth = get_azimuth(latitude, longitude, time_utc)

print(f"Date & Time (Local): {time}")
print(f"Solar Altitude: {altitude:.2f}°")
print(f"Solar Azimuth: {azimuth:.2f}°")
