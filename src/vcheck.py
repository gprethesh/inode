import os
import zipfile
import hashlib
import requests

def check_virus_total(hash_str):
    api_key = '47999aa4e294f9d31a53d4834bb22b836266a812c19dffe530488c065527861f'
    url = f'https://www.virustotal.com/api/v3/files/{hash_str}'
    headers = {
        'x-apikey': api_key
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result_data = response.json()
        if result_data['data']['attributes']['last_analysis_stats']['malicious'] > 0:
            return False  # Virus found
        else:
            return True  # No virus found
    elif response.status_code == 404:
        print('Hash not found in VirusTotal database.')
        return False  # Assuming it's unsafe if not found
    else:
        print(f'Error: {response.status_code}')
        print(response.text)
        return False  # Assuming it's unsafe if there's an error

def compute_sha256(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def next_folder_number(base_dir):
    existing_folders = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.isdigit()]
    existing_folders = sorted(existing_folders, key=int)
    if existing_folders:
        return str(int(existing_folders[-1]) + 1)
    return "0"

def extract_zip(file_path):
    if not zipfile.is_zipfile(file_path):
        print(f'{file_path} is not a zip file.')
        return
    
    file_hash = compute_sha256(file_path)
    print(f'SHA-256 Hash: {file_hash}')

    is_safe = check_virus_total(file_hash)
    if not is_safe:
        print(f'The file {file_path} is potentially malicious, extraction aborted.')
        return

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            # Check for nested zip files
            if member.endswith('.zip'):
                print(f'Error: Nested zip file {member} found. Extraction aborted.')
                return

    # If all checks pass, then create the necessary directories and proceed with extraction
    todo_dir = os.path.join(os.getcwd(), 'TODO')
    if not os.path.exists(todo_dir):
        os.makedirs(todo_dir)

    folder_number = next_folder_number(todo_dir)
    extraction_dir = os.path.join(todo_dir, folder_number)
    os.makedirs(extraction_dir)

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            if '__MACOSX' not in member:
                zip_ref.extract(member, extraction_dir)
        print(f'Files extracted to {extraction_dir}')

script_dir = os.path.dirname(os.path.abspath(__file__))

source = os.path.join(script_dir, 'test.zip')

print("zip_file_path", source)
extract_zip(source)
