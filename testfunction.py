import os
from datetime import datetime
import json

now = datetime.now()
path_time_stamp = now.strftime("%d_%m_%y"+"h2")
payload = {
    "timestamp": "sdfsdfsdf",
    "currentX":  123213,
    "currentY": 123123123,
}
json_str = json.dumps(payload)
perfixed_json = f"*{json_str}"

path_file_by_date = f"./data/result/{path_time_stamp}/data.txt"
path_folder_by_date = f"./data/result/{path_time_stamp}"
filepath_by_date = os.path.join(os.getcwd(), path_folder_by_date)
check_file_path = os.path.isdir(filepath_by_date)
print(check_file_path)
if check_file_path == False:
    os.mkdir(path_folder_by_date)
    with open(path_file_by_date, mode='w', newline='') as text_f:
        text_f.write(perfixed_json+"\n")

else:
     with open(path_file_by_date, mode='a', newline='', encoding='utf-8') as text_f:
         text_f.writelines(perfixed_json+"\n")