#%%
import requests
from requests.auth import HTTPBasicAuth
import os
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import getpass
from tqdm import tqdm
import concurrent.futures
import time

#%%
def download_single_file(session, file_url, local_path):
    """
    Download a single file with the given session
    
    Parameters:
    -----------
    session : requests.Session
        Authenticated session
    file_url : str
        URL of the file to download
    local_path : str
        Local path to save the file
    
    Returns:
    --------
    tuple
        (success, file_name, error_message)
    """
    try:
        file_name = os.path.basename(file_url)
        
        # Skip if file already exists and has content
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            return (True, file_name, "File already exists, skipped")
        
        response = session.get(file_url, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive chunks
                    f.write(chunk)
        
        return (True, file_name, "Success")
    except requests.exceptions.RequestException as e:
        return (False, os.path.basename(file_url), str(e))
    except Exception as e:
        return (False, os.path.basename(file_url), str(e))

def download_matching_files(base_url, username, password, pattern="t2m_elvcorr_2001.*.nc", 
                           dest_path="downloads", max_workers=4):
    """
    Download files matching the pattern from an HTTPS server with authentication,
    using parallel downloads
    
    Parameters:
    -----------
    base_url : str
        URL of the server directory
    username : str
        Username for authentication
    password : str
        Password for authentication
    pattern : str
        Regex pattern to match filenames
    dest_path : str
        Destination directory path for downloaded files
    max_workers : int
        Maximum number of parallel downloads
    """
    # Create a session with authentication
    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)
    
    # Create destination directory
    os.makedirs(dest_path, exist_ok=True)
    
    print(f"Connecting to {base_url}...")
    
    try:
        # Try to get directory listing
        response = session.get(base_url)
        response.raise_for_status()
        
        # Parse HTML to find links
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [link.get('href') for link in soup.find_all('a')]

        # split links to get only the file names
        links = [link.split('/')[-1] for link in links]
        
        # Filter links matching our pattern
        matching_files = [link for link in links if link and re.match(pattern, link)]
        
        if not matching_files:
            print("No matching files found in directory listing.")
            return
            
        num_files = len(matching_files)
        print(f"Found {num_files} matching files.")
        
        # Prepare download tasks
        download_tasks = []
        for file_name in matching_files:
            file_url = urljoin(base_url, file_name)
            local_path = os.path.join(dest_path, file_name)
            download_tasks.append((file_url, local_path))
        
        # Download files in parallel
        successful = 0
        failed = 0
        failed_files = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Start the download tasks
            future_to_url = {
                executor.submit(download_single_file, session, url, path): url 
                for url, path in download_tasks
            }
            
            # Process results with progress bar
            with tqdm(total=num_files, desc="Downloading files", unit="file") as pbar:
                for future in concurrent.futures.as_completed(future_to_url):
                    url = future_to_url[future]
                    try:
                        success, file_name, message = future.result()
                        if success:
                            successful += 1
                        else:
                            failed += 1
                            failed_files.append((file_name, message))
                            print(f"\nError downloading {file_name}: {message}")
                    except Exception as e:
                        failed += 1
                        file_name = os.path.basename(url)
                        failed_files.append((file_name, str(e)))
                        print(f"\nException while downloading {file_name}: {e}")
                    pbar.update(1)
        
        # Report results
        print(f"\nDownload complete. {successful} files downloaded successfully, {failed} files failed.")
        if failed > 0:
            print("\nFailed files:")
            for file_name, error in failed_files:
                print(f"- {file_name}: {error}")
            
    except requests.exceptions.RequestException as e:
        print(f"Error accessing server: {e}")

if __name__ == "__main__":
    server_url = input("Enter server URL (e.g., https://example.com/data/): ")
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    dest_path = input("Enter destination directory path [downloads]: ") or "downloads"
    pattern = input("Enter file pattern e.g., [t2m_elvcorr_2000.*.nc]: ") or r"t2m_elvcorr_2000.*.nc"
    max_workers = input("Enter maximum number of parallel downloads [4]: ")
    
    try:
        max_workers = int(max_workers) if max_workers else 4
    except ValueError:
        max_workers = 4
        print("Invalid number, using default (4 parallel downloads)")
    
    start_time = time.time()
    download_matching_files(server_url, username, password, pattern, dest_path, max_workers)
    elapsed_time = time.time() - start_time
    print(f"Total download time: {elapsed_time:.2f} seconds")