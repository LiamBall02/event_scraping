import os

def rename_files():
    # Get all files in current directory
    files = os.listdir('.')
    
    # Filter for files without dots in their names (except the script itself)
    files_to_rename = [f for f in files if os.path.isfile(f) and '.' not in f and f != 'rename_files.py']
    
    # Rename each file
    for file in files_to_rename:
        new_name = f"{file}.json"
        try:
            os.rename(file, new_name)
            print(f"Renamed {file} to {new_name}")
        except Exception as e:
            print(f"Error renaming {file}: {str(e)}")

if __name__ == "__main__":
    rename_files() 