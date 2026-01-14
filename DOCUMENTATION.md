# 📚 Project Documentation

This document provides a deeper dive into the configuration and logic of the Bulk File Downloader.

## 🔧 Configuration (`config.py`)

All customizable settings are located in `config.py`. This modular approach allows you to modify the application's behavior without touching the core logic.

### Core Settings

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BATCH_SIZE` | `50` | Defines how many URLs are processed before the progress is saved to `progress.json`. If the script crashes, you lose at most this many items of progress. |
| `MAX_WORKERS` | `8` | The number of parallel threads. Increase this if you have high bandwidth, decrease if you want to be gentle on the server. |
| `TIMEOUT` | `60` | Request timeout in seconds. If a server doesn't respond within this time, it's considered a failure (will trigger retry). |
| `MAX_RETRY` | `3` | Number of times to retry a failed download before giving up. |

### Path & CSV Settings

| Variable | Default | Description |
| :--- | :--- | :--- |
| `DOWNLOAD_DIR` | `"downloads"` | The output directory. The script will automatically create this folder if it doesn't exist. |
| `PROGRESS_FILE` | `"progress.json"` | JSON file used to store the index of the last processed batch. |
| `CSV_URL_COL` | `"url"` | The exact header name (case-sensitive) in your CSV file that contains the download links. |
| `CSV_TITLE_COL` | `"Title"` | The exact header name for the file title/description. This is used in logs to help identify files. |

## 🧠 Logic Flow

### 1. Initialization
- The script checks for the existence of the CSV file.
- It attempts to load `progress.json`.
  - If found, it reads the `last_index` to resume from where it stopped.
  - If not found, it starts from index 0.

### 2. Processing Loop
- The script iterates through the CSV rows in chunks determined by `BATCH_SIZE`.
- For each batch, it spawns a `ThreadPoolExecutor` with `MAX_WORKERS`.
- URLs are submitted to the thread pool for concurrent downloading.

### 3. Downloading Strategy (`process_single_url`)
1.  **Validation**: Checks if the URL is valid and not empty.
2.  **Request**: Sends a GET request with stream enabled. Behaving like a browser (`User-Agent` is set).
3.  **Filename Detection**:
    - **Step A**: Checks the `Content-Disposition` header from the server (best for dynamic URLs).
    - **Step B**: Falls back to extracting the basename from the URL path.
    - **Step C**: If both fail, generates a timestamped filename (e.g., `download_170123...bin`).
4.  **Writing**:
    - Writes content to a `.tmp` file first to prevent corrupt partial files.
    - Once fully downloaded, renames `.tmp` to the final filename.
5.  **Logging**:
    - **Success**: Recorded in `success.log` with timestamp, URL, Filename, Size, and Title.
    - **Failure**: Recorded in `failed.log` with error details.

### 4. Progress Saving
- Progress is **only** saved after a full batch completes. This ensures that if you stop the script, you continue safely from the start of the last unfinished batch.

## ⚠️ Notes

- **Deleting Progress**: If you want to re-download everything, simply delete the `progress.json` file.
- **Filename Collisions**: Currently, if a file with the same name exists, the script **overwrites** it. Be cautious if multiple URLs resolve to the same filename.
