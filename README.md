# Bulk File Downloader

High-performance, multi-threaded Python script for bulk downloading files from a CSV list. Features include resumable downloads, smart retries, and detailed logging.

## 🚀 Features

- **Multi-threaded**: Downloads multiple files concurrently for maximum speed.
- **Resumable**: Tracks progress in `progress.json`. Interrupted? Just run it again, and it continues where it left off.
- **Smart Retries**: Handles temporary network errors with exponential backoff.
- **Logging**:
  - `success.log`: Records successfully downloaded files.
  - `failed.log`: Records failed downloads with error messages.
- **Configurable**: Easily adjust threads, batch size, and timeouts in `config.py`.
- **Title Support**: Can log a custom "Title" for each URL from the CSV.

## 📋 Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## 🛠️ Installation

1. **Clone or Download** this repository.
2. **Set up a Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Configuration

Open `config.py` to customize the downloader behaviors:

- **`BATCH_SIZE`**: Number of items to process before saving progress (Default: 50).
- **`MAX_WORKERS`**: Number of concurrent download threads (Default: 8).
- **`DOWNLOAD_DIR`**: Folder where files will be saved.
- **`CSV_URL_COL`**: Name of the URL column in your CSV.
- **`CSV_TITLE_COL`**: Name of the Title column in your CSV (optional).

## 🏃 Usage

1. **Prepare your CSV file** (default: `links.csv`).
   - Must contain at least a URL column (header name defined in `config.py`, default: `url`).
   - Optionally, add a Title column (header name defined in `config.py`, default: `Title`).

   **Example `links.csv`**:
   ```csv
   url,Title
   https://example.com/file1.zip,File One
   https://example.com/image.png,My Image
   ```

2. **Run the script**:
   ```bash
   python main.py
   ```

3. **Check results**:
   - Files will be in the `downloads/` folder (or whatever you set in config).
   - Check `success.log` for details.
   - Check `failed.log` for errors.

## 🔄 Reseting Progress

To restart the download process from the beginning:
1. Delete `progress.json`.
2. Run the script again.

## 📝 License

Checking `links.csv`...
Done.
