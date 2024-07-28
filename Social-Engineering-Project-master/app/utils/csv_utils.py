import csv
import os
from typing import List


async def save_csv_to_directory(data: List[dict], filename: str):
    directory = "./saved_csvs"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        if data:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            for item in data:
                writer.writerow(item)
    
    return filepath


async def save_formatted_csv_to_directory(data: List[dict], filename: str, fields: List[str]):
    directory = "./saved_csvs"
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    
    with open(filepath, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for item in data:
            writer.writerow({field: item.get(field, '') for field in fields})
    
    return filepath


