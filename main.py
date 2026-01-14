import os
import json
import csv
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
# ========================
# Constants & Setup
# ========================
SUCCESS_LOG = "success_log.csv"
FAILED_LOG = "failed_log.csv"
LOG_LOCK = threading.Lock()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ========================
# Logging Functions
# ========================
def init_logs():
    """Initialize log files with headers if they don't exist."""
    with LOG_LOCK:
        if not os.path.exists(SUCCESS_LOG):
            with open(SUCCESS_LOG, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["TITLE", "URL", "LOG"])
                
        if not os.path.exists(FAILED_LOG):
            with open(FAILED_LOG, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["TITLE", "URL", "LOG"])

def log_success(url, filename, size, title=None):
    # Log format: TITLE, URL, LOG (filename + size)
    log_msg = f"Downloaded -> {filename} ({size} bytes)"
    with LOG_LOCK:
        with open(SUCCESS_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([title or "", url, log_msg])

def log_failure(url, error_msg, title=None):
    # Log format: TITLE, URL, LOG (error message)
    with LOG_LOCK:
        with open(FAILED_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([title or "", url, error_msg])

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
    init_logs()
    
    # 1. Load Data (Auto-detect format)
    df = None
    input_files = [
        f"{INPUT_FILENAME_BASE}.xlsx",
        f"{INPUT_FILENAME_BASE}.xls",
        f"{INPUT_FILENAME_BASE}.csv"
    ]
    
    found_file = None
    for f_path in input_files:
        if os.path.exists(f_path):
            found_file = f_path
            print(f"📄 Found input file: {found_file}")
            break
            
    if not found_file:
        print(f"❌ Error: Input file not found! Please create '{INPUT_FILENAME_BASE}.xlsx', .xls, or .csv'")
        return

    try:
        if found_file.endswith((".xlsx", ".xls")):
            df = pd.read_excel(found_file)
        else:
            # CSV with fallback encoding
            try:
                # Try UTF-8 with error_bad_lines=False (for pandas < 1.3) or on_bad_lines='skip'
                # Note: 'on_bad_lines' is for pandas >= 1.3. For older versions use error_bad_lines=False.
                # using on_bad_lines='warn' or 'skip' is safer for messy CSVs
                try:
                    df = pd.read_csv(found_file, encoding="utf-8", on_bad_lines='skip')
                except TypeError: # Older pandas
                    df = pd.read_csv(found_file, encoding="utf-8", error_bad_lines=False)
            except UnicodeDecodeError:
                print("⚠️ UTF-8 decoding failed. Retrying with ISO-8859-1...")
                try:
                    try:
                        df = pd.read_csv(found_file, encoding="ISO-8859-1", on_bad_lines='skip')
                    except TypeError:
                        df = pd.read_csv(found_file, encoding="ISO-8859-1", error_bad_lines=False)
                except Exception as e:
                    print(f"❌ Error reading CSV (ISO-8859-1 failed): {e}")
                    return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    # Clean header names (strip whitespace)
    df.columns = df.columns.str.strip()

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
