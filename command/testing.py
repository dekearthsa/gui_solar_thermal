from datetime import datetime
import os 
import json 
now = datetime.now()
path_time_stamp = now.strftime("%d_%m_%y"+"_"+"hTest")
path_file_by_date_gyro = f"../data/calibrate_gyro/{path_time_stamp}.txt" 
# path_folder_by_date_gryo = f"../data/calibrate_gyro/{path_time_stamp}"

adding_path_data_gyro = {
            "timestamp": path_time_stamp,
            "elevation":  125.54,
            "azimuth": 484.55,
        }

json_str_gyro = json.dumps(adding_path_data_gyro)
perfixed_gyro_json = f"*{json_str_gyro}"


with open(path_file_by_date_gyro, mode='a', newline='') as text_f:
    text_f.write(perfixed_gyro_json+"\n")
