import os
from datetime import datetime
import csv
import json

now = datetime.now()
path_time_stamp = now.strftime("%d_%m_%y_%M")


adding_time = {
    "test": 5,
    "test2": 5
}

fieldnames = adding_time.keys()

path_file_by_date = f"./data/result/{path_time_stamp}.csv"
filepath_by_date = os.path.join(os.getcwd(), path_file_by_date)
check_file_path = os.path.isfile(filepath_by_date)


if check_file_path == False: ## create csv and write
    with open(filepath_by_date, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(adding_time.keys())
        writer.writerow(adding_time.values())


else: ## write csv
    with open(filepath_by_date, mode='a', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(adding_time)
