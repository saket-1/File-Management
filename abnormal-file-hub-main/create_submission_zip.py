#!/usr/bin/env python3

import os
import zipfile
import datetime
import getpass
from pathlib import Path
import pathspec # Used for .gitignore parsing

# --- Configuration ---
# Placeholder for username, ideally replace with actual logic if possible
DEFAULT_USERNAME = getpass.getuser().lower().replace(" ", "_") # Get system username as default
# Define files/directories to explicitly exclude beyond .gitignore
# (e.g., the script itself, potentially large data/media if not needed for submission)
EXPLICIT_EXCLUDES = [
    ".git", # Always exclude .git directory
    ".DS_Store",
    "*.pyc",
    "__pycache__",
    "backend/data/", # Exclude potentially large db file
    "backend/media/", # Exclude uploaded media
    "backend/staticfiles/", # Exclude collected static files (can be regenerated)
    "backend/venv/", # Exclude backend venv
    "frontend/node_modules/", # Exclude frontend dependencies
    "frontend/build/", # Exclude frontend build artifacts
    "*.zip", # Exclude zip files
    "create_submission_zip.py", # Exclude this script itself
    ".env*", # Exclude all env files
    "!.env.example", # But maybe include example env files if they exist
    ".vscode/",
    ".idea/",
]
# Define a size threshold for warning (e.g., 20MB)
SIZE_WARNING_THRESHOLD = 20 * 1024 * 1024 # 20 MB
# --- End Configuration ---

def get_gitignore_spec(root_dir):
    """ Loads and parses the .gitignore file. """
    gitignore_path = root_dir / '.gitignore'
    patterns = []
    if gitignore_path.is_file():
        with open(gitignore_path, 'r') as f:
            patterns = f.read().splitlines()
    # Combine gitignore patterns with explicit excludes
    all_patterns = patterns + EXPLICIT_EXCLUDES
    return pathspec.PathSpec.from_lines('gitwildmatch', all_patterns)

def create_submission_zip():
    """ Creates the submission zip file. """
    project_root = Path(__file__).parent.resolve()
    spec = get_gitignore_spec(project_root)
    
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    zip_filename = f"{DEFAULT_USERNAME}_{today_str}.zip"
    zip_filepath = project_root / zip_filename
    
    total_size = 0
    included_files_count = 0
    
    print(f"Creating submission zip file: {zip_filename}...")
    
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in project_root.rglob('*'):
                # Get path relative to project root for matching and adding to zip
                relative_path = file_path.relative_to(project_root)
                
                # Skip if the path matches any exclude pattern
                if spec.match_file(str(relative_path)) or spec.match_file(str(file_path)):
                    # print(f"Excluding: {relative_path}")
                    continue
                    
                # Skip directories themselves, but process their contents
                if file_path.is_dir():
                    continue
                
                # Add file to zip, preserving path structure
                print(f"  Adding: {relative_path}")
                zipf.write(file_path, arcname=relative_path)
                total_size += file_path.stat().st_size
                included_files_count += 1

        print("\n--- Zip File Contents Summary ---")
        with zipfile.ZipFile(zip_filepath, 'r') as zipf:
            zipf.printdir()

        print(f"\nSuccessfully created {zip_filename}")
        print(f"Total files included: {included_files_count}")
        total_size_mb = total_size / (1024 * 1024)
        print(f"Total uncompressed size: {total_size_mb:.2f} MB")

        if total_size > SIZE_WARNING_THRESHOLD:
            print("\n--- WARNING --- ")
            print(f"The zip file content size ({total_size_mb:.2f} MB) exceeds the recommended threshold of {SIZE_WARNING_THRESHOLD / (1024 * 1024):.0f} MB.")
            print("Please double-check if large files (like databases, media, node_modules, venv) were unintentionally included.")

    except Exception as e:
        print(f"\nError creating zip file: {e}")
        if zip_filepath.exists():
            os.remove(zip_filepath) # Clean up partially created zip

if __name__ == "__main__":
    # Add dependency check for pathspec
    try:
        import pathspec
    except ImportError:
        print("Error: 'pathspec' library is required. Please install it:")
        print("pip install pathspec")
        # Or add it to your backend requirements.txt if appropriate
        exit(1)
        
    create_submission_zip() 