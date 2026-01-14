# Bulk File Downloader

High-performance, multi-threaded Python script for bulk downloading files from a CSV list. Features include resumable downloads, smart retries, and detailed logging.

## 🚀 Features

- **Format Support**: Supports input lists in `.xlsx`, `.xls`, and `.csv` formats.
- **Multi-threaded**: Downloads multiple files concurrently for maximum speed.
- **Resumable**: Tracks progress in `progress.json`. Interrupted? Just run it again, and it continues where it left off.
- **Smart Retries**: Handles temporary network errors with exponential backoff.
- **Logging**:
  - `success_log.csv`: Records successfully downloaded files (Columns: TITLE, URL, LOG).
  - `failed_log.csv`: Records failed downloads (Columns: TITLE, URL, LOG).
- **Configurable**: Easily adjust threads, batch size, and timeouts in `config.py`.
- **Title Support**: Can log a custom "Title" for each URL from the input file.

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
- **`DOWNLOAD_DIR`**: Folder where files will be saved (Default: `images`, but can be anything like `downloads`, `fonts`, etc).
- **`INPUT_FILENAME_BASE`**: Base name of input file to search for (Default: `links`).
- **`CSV_URL_COL`**: Name of the URL column in your input file.
- **`CSV_TITLE_COL`**: Name of the Title column in your input file (optional).

## 🏃 Usage

1. **Prepare your input file** (e.g., `links.xlsx` or `links.csv`).
   - Must contain at least a URL column (header name defined in `config.py`, default: `FontImgUrl`).
   - Optionally using a Title column (default: `TITLE`).

2. **Run the script**:
   ```bash
   python main.py
   ```
   The script looks for `links.xlsx` first, then `links.xls`, then `links.csv`.

3. **Check results**:
   - Files will be in the `images/` folder (or whatever you set in config).
   - Check `success_log.csv` for details.
   - Check `failed_log.csv` for errors.

## 🔄 Reseting Progress

To restart the download process from the beginning:
1. Delete `progress.json`.
2. Run the script again.

## 📝 License

This project is open-source. Feel free to use and modify it for your personal or commercial projects.
