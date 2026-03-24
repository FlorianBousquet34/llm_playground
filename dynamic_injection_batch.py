import json
import os
from time import sleep

from dotenv import load_dotenv

from src.code_parser_neo4j import refresh_code_files
from src.data_injection_neo4j import refresh_files
from simple_file_checksum import get_checksum

# FIXME remove no longer indexed files

INDEXATION_CONFIGURATION_FILE = "data/indexation-configuration.json"

if __name__ == "__main__":
    # Load the environment variables
    load_dotenv()
    
    index_path = 'data/file-index.json'
    code_index_path = 'data/code-index.json'
    file_index = {}
    code_file_index= {}
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            file_index = json.loads(f.read())
    if os.path.exists(code_index_path):
        with open(code_index_path, 'r') as f:
            code_file_index = json.loads(f.read())

    while True:
        # retrieve conf
        with open(INDEXATION_CONFIGURATION_FILE, "r") as f:
            conf_data = json.loads(f.read())
        doc_folder_to_index = conf_data["documentation_folders"]["text"]
        js_code_folder_to_index = conf_data["code_folders"]["javascript"]
        index_frequency = conf_data["index_frequency"]
        # finding modified / created files
        # text
        files_modified = []
        actual_directory = doc_folder_to_index.copy()
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

        # code
        files_modified = []
        actual_directory = js_code_folder_to_index.copy()
        while len(actual_directory) > 0:
            found_dirs = []
            for curr_folder in actual_directory:
                for file_name in os.listdir(curr_folder):
                    file_path = os.path.join(curr_folder, file_name)
                    if os.path.isfile(file_path):
                        # compute checksum
                        checksum = get_checksum(file_path)
                        # compare to index
                        existing_checksum = code_file_index.get(file_path, None)
                        if existing_checksum is None or existing_checksum != checksum:
                            files_modified.append(file_path)
                        code_file_index[file_path] = checksum
                    else:
                        found_dirs.append(f"{curr_folder}/{file_name}")
            actual_directory = found_dirs
        # finding deleted files
        files_unmodified = list(set(code_file_index.keys()) - set(files_modified))
        files_deleted = []
        for file_path in files_unmodified:
            if not os.path.exists(file_path):
                files_deleted.append(file_path)
                code_file_index.pop(file_path)
                
        if len(files_deleted) > 0 or len(files_modified) > 0:
            refresh_code_files(files_deleted, files_modified, True)
            with open(code_index_path, 'w') as f:
                json.dump(code_file_index, f)
        sleep(index_frequency)