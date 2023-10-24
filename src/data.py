import os
import zipfile
import csv
from hashlib import sha256
from tqdm import tqdm
from vcheck import check_virus_total

def compute_sha256(file_path):
    """Compute the SHA256 hash of a file."""
    with open(file_path, 'rb') as f:
        return sha256(f.read()).hexdigest()

def split_data(source_dir, target_dir, hash_csv_path, chunk_size_MB=10):
    """Split data into zip chunks and record hashes."""
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    current_zip_path = os.path.join(target_dir, 'chunk_0.zip')
    zipf = zipfile.ZipFile(current_zip_path, 'a')
    current_size_MB = 0
    chunk_index = 0
    hash_list = []

    total_files = sum([len(files) for subdir, dirs, files in os.walk(source_dir)])
    with tqdm(total=total_files, desc="Processing Images") as pbar:
        for label in os.listdir(source_dir):
            label_dir = os.path.join(source_dir, label)
            if os.path.isdir(label_dir):
                for image_file in os.listdir(label_dir):
                    image_path = os.path.join(label_dir, image_file)
                    arcname = os.path.join(label, image_file)  # This ensures labels are preserved in the zip structure

                    # If current chunk exceeds size, create a new zip
                    if current_size_MB + os.path.getsize(image_path) / (1024 * 1024) > chunk_size_MB:
                        zipf.close()
                        chunk_hash = compute_sha256(current_zip_path)
                        print(f"SHA256 of {current_zip_path}: {chunk_hash}")
                        hash_list.append((current_zip_path, chunk_hash))

                        chunk_index += 1
                        current_zip_path = os.path.join(target_dir, f'chunk_{chunk_index}.zip')
                        zipf = zipfile.ZipFile(current_zip_path, 'a')
                        current_size_MB = 0

                    # Add image to the current zip file
                    zipf.write(image_path, arcname=arcname)
                    current_size_MB += os.path.getsize(image_path) / (1024 * 1024)

                    pbar.update(1)

        # Compute hash for the last zip
        zipf.close()
        chunk_hash = compute_sha256(current_zip_path)
        print(f"SHA256 of {current_zip_path}: {chunk_hash}")
        hash_list.append((current_zip_path, chunk_hash))

    # Write hashes to CSV
    with open(hash_csv_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Zip File", "SHA256 Hash"])
        for record in hash_list:
            writer.writerow(record)


def next_project_name(base_dir):
    """Get the next project name (number) based on existing projects."""
    existing_projects = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d.isdigit()]
    existing_projects = sorted(existing_projects, key=int)
    if existing_projects:
        return str(int(existing_projects[-1]) + 1)
    return "0"

# Determine the absolute path to the directory containing data.py
script_dir = os.path.dirname(os.path.abspath(__file__))

# Determine the next project name
project_name = next_project_name(script_dir)

# Define directories and paths
project_directory = os.path.join(script_dir, project_name)
source_directory = os.path.join(script_dir, 'TODO/0/test')
target_directory = os.path.join(project_directory, 'saved')
hash_directory = os.path.join(project_directory, 'hash')
hash_csv = os.path.join(hash_directory, 'hashes.csv')

# Create necessary directories
if not os.path.exists(target_directory):
    os.makedirs(target_directory)
if not os.path.exists(hash_directory):
    os.makedirs(hash_directory)

# Execute the split_data function
split_data(source_directory, target_directory, hash_csv)

