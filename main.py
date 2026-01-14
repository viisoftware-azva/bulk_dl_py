import os
import json
import time
import requests
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
from urllib.parse import urlparse
from datetime import datetime
from config import *

# ========================
# Constants & Setup
# ========================
SUCCESS_LOG = "success.log"
FAILED_LOG = "failed.log"
LOG_LOCK = threading.Lock()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ========================
# Logging Functions
# ========================
def log_success(url, filename, size, title=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title_str = f" | Title: {title}" if title else ""
    message = f"[{timestamp}] SUCCESS: {url} -> {filename} ({size} bytes){title_str}"
    with LOG_LOCK:
        with open(SUCCESS_LOG, "a", encoding="utf-8") as f:
            f.write(message + "\n")

def log_failure(url, error_msg, title=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title_str = f" | Title: {title}" if title else ""
    message = f"[{timestamp}] FAILED: {url} | Error: {error_msg}{title_str}"
    with LOG_LOCK:
        with open(FAILED_LOG, "a", encoding="utf-8") as f:
            f.write(message + "\n")

# ========================
# Network Session Setup
# ========================
def create_session():
    session = requests.Session()
    
    # Smart Retry with Backoff
    retry_strategy = Retry(
        total=MAX_RETRY,
        backoff_factor=1,  # sleep = {backoff factor} * (2 ** ({number of total retries} - 1))
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    # Default Headers
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    return session

# ========================
# Download Logic
# ========================
def get_filename_from_url(url, response=None):
    filename = None
    
    # Try Content-Disposition
    if response and "Content-Disposition" in response.headers:
        import re
        cd = response.headers["Content-Disposition"]
        fname = re.findall("filename=(.+)", cd)
        if fname:
            filename = fname[0].strip(' "')
            
    # Fallback to URL
    if not filename:
        path = urlparse(url).path
        filename = os.path.basename(path)
    
    # Final fallback
    if not filename or filename.strip() == "":
        filename = f"download_{int(time.time())}_{threading.get_ident()}.bin"
        
    return filename

def process_single_url(session, url, title=None):
    """
    Handles the download of a single URL.
    Returns: (is_success, url, message)
    """
    try:
        url = str(url).strip()
        if not url or url.lower() == "nan":
            return False, url, "Empty URL"

        if not url.startswith(("http://", "https://")):
            log_failure(url, "Invalid URL format", title)
            return False, url, "Invalid Format"
        
        # Download
        with session.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            
            filename = get_filename_from_url(url, r)
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            # Use temporary file to avoid partial downloads on corruptions
            temp_filepath = filepath + ".tmp"
            
            total_size = 0
            with open(temp_filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        total_size += len(chunk)
            
            # Rename temp to actual
            if os.path.exists(filepath):
                os.remove(filepath) # Overwrite if exists
            os.rename(temp_filepath, filepath)
            
            log_success(url, filename, total_size, title)
            return True, url, "OK"

    except Exception as e:
        log_failure(url, str(e), title)
        return False, url, str(e)

# ========================
# Main Execution
# ========================
def main():
    # 1. Load CSV
    if not os.path.exists("links.csv"):
        print("❌ Error: 'links.csv' not found!")
        return

    try:
        df = pd.read_csv("links.csv")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    if CSV_URL_COL not in df.columns:
        print(f"❌ Error: CSV must contain '{CSV_URL_COL}' column (Check config.py)")
        return

    # 2. Load Progress
    start_index = 0
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
                start_index = data.get("last_index", 0)
        except:
            start_index = 0

    total_items = len(df)
    print(f"▶ Resuming from index: {start_index} / {total_items}")
    print(f"▶ Workers: {MAX_WORKERS} | Batch Size: {BATCH_SIZE}")

    if start_index >= total_items:
        print("🎉 Nothing to download (Already completed)")
        return

    # 3. Setup Session & ThreadPool
    session = create_session()
    
    # 4. Processing Loop
    # We iterate in chunks (BATCH_SIZE)
    # The progress is saved ONLY after a full batch is submitted and completed.
    
    # Function to get title safely (if column exists)
    has_title_col = CSV_TITLE_COL in df.columns
    if not has_title_col:
        print(f"⚠️ Warning: Column '{CSV_TITLE_COL}' not found in CSV. Titles will be empty.")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        for i in range(start_index, total_items, BATCH_SIZE):
            # Create batch slice
            batch_slice = df.iloc[i : i + BATCH_SIZE]
            
            # List of futures
            futures = []
            
            # Submit tasks
            for idx, row in batch_slice.iterrows():
                url = row[CSV_URL_COL]
                title = row[CSV_TITLE_COL] if has_title_col else None
                futures.append(executor.submit(process_single_url, session, url, title))
            
            # Wait for batch to complete and show progress
            # We use tqdm manually here for the batch
            desc = f"Batch {i}-{min(i+BATCH_SIZE, total_items)}"
            for future in tqdm(as_completed(futures), total=len(futures), desc=desc, leave=False):
                result = future.result()
                # result is (is_success, url, msg)
                # You could print errors here if you want verbose output

            # Save check point
            next_index = min(i + BATCH_SIZE, total_items)
            with open(PROGRESS_FILE, "w") as f:
                json.dump({"last_index": next_index}, f)

    print("\n🎉 ALL TASKS FINISHED. Check 'success.log' and 'failed.log'.")

if __name__ == "__main__":
    main()
