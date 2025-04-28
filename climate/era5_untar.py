"""
Script to extract all tar files from a source directory to a target directory.
Simply modify the source_dir and target_dir variables below to specify your folders.
This script shows progress for both overall extraction and for individual files within each tar.
"""

import os
import tarfile
from pathlib import Path
import sys
from tqdm import tqdm

# ===== CONFIGURE THESE PATHS =====
source_dir = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/data/GEMLST_MODIS/ERA5"  # Change this to your source folder path
target_dir = "/mnt/i/SCIENCE-IGN-ALL/AVOCA_Group/1_Personal_folders/3_Shunan/data/GEMLST_MODIS/ERA5"   # Change this to your target folder path
# =================================

def untar_files(source_dir, target_dir):
    """
    Recursively find and extract all .tar files from source_dir to target_dir
    while preserving the folder structure and showing nested progress bars:
    - Outer progress bar for all tar files
    - Inner progress bar for files within each tar
    """
    source_dir = Path(source_dir).resolve()
    target_dir = Path(target_dir).resolve()
    
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist", file=sys.stderr)
        return False
    
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # First collect all tar files
    print("Finding all tar files...")
    tar_files = []
    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.tar'):
                tar_path = Path(root) / file
                rel_path = Path(root).relative_to(source_dir)
                extract_dir = target_dir / rel_path
                tar_files.append((tar_path, extract_dir))
    
    if not tar_files:
        print("No .tar files found in the source directory")
        return False
    
    # Now extract each file with a progress bar
    print(f"Found {len(tar_files)} tar files. Beginning extraction...")
    
    # Outer progress bar for all tar files
    for tar_path, extract_dir in tqdm(tar_files, desc="Extracting tar files"):
        # Create extract directory if it doesn't exist
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract the tar file with progress for internal files
        try:
            with tarfile.open(tar_path) as tar:
                # Get list of members
                members = tar.getmembers()
                num_files = len(members)
                
                # Display tar file name
                tar_name = tar_path.name
                print(f"\nExtracting {tar_name} ({num_files} files)")
                
                # Inner progress bar for files within this tar
                for member in tqdm(members, desc=f"Files in {tar_name}", leave=False):
                    try:
                        tar.extract(member, path=extract_dir, filter='data')
                    except Exception as e:
                        print(f"  Error extracting '{member.name}': {e}", file=sys.stderr)
                
        except Exception as e:
            print(f"Error opening tar file '{tar_path}': {e}", file=sys.stderr)
    
    print(f"Extraction complete! Processed {len(tar_files)} tar files")
    return True

if __name__ == "__main__":
    print(f"Source directory: {source_dir}")
    print(f"Target directory: {target_dir}")
    
    if untar_files(source_dir, target_dir):
        print("Extraction completed successfully!")
    else:
        print("Extraction process had issues. Check the output for details.")
        sys.exit(1)