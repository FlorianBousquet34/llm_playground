import json
import os
from time import sleep

from data_injection_neo4j import refresh_files
from simple_file_checksum import get_checksum

index_path = './data/file-index.json'
file_index = {}
if os.path.exists(index_path):
    with open(index_path, 'r') as f:
        file_index = json.loads(f.read())
    
folder_to_index = "./data/file-repository"

while True:
    # finding modified / created files
    files_modified = []
    actual_directory = [folder_to_index]
    while len(actual_directory) > 0:
        found_dirs = []
        for curr_folder in actual_directory:
            for file_name in os.listdir(curr_folder):
                file_path = os.path.join(curr_folder, file_name)
                if os.path.isfile(file_path):
                    # compute checksum
                    checksum = get_checksum(file_path)
                    # compare to index
                    existing_checksum = file_index.get(file_path, None)
                    if existing_checksum is None or existing_checksum != checksum:
                        files_modified.append(file_path)
                    file_index[file_path] = checksum
                else:
                    found_dirs.append(f"{curr_folder}/{file_name}")
        actual_directory = found_dirs
    # finding deleted files
    files_unmodified = list(set(file_index.keys()) - set(files_modified))
    files_deleted = []
    for file_path in files_unmodified:
        if not os.path.exists(file_path):
            files_deleted.append(file_path)
            file_index.pop(file_path)
            
    if len(files_deleted) > 0 or len(files_modified) > 0:
        refresh_files(files_deleted + files_modified)
        with open(index_path, 'w') as f:
            json.dump(file_index, f)
    sleep(5)