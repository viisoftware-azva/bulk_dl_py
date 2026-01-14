
BATCH_SIZE = 50
MAX_WORKERS = 8
TIMEOUT = 60
SLEEP_SECONDS = 1
MAX_RETRY = 3

# ========================
# Path Settings
# ========================
DOWNLOAD_DIR = "images"  # Folder hasil download (Otomatis dibuat jika belum ada)
PROGRESS_FILE = "progress.json"
INPUT_FILENAME_BASE = "links" # Nama file input (tanpa ekstensi, akan mencari .xlsx, .xls, .csv)

# CSV Column Names
CSV_URL_COL = "FontImgUrl"      # Nama kolom untuk URL (Case sensitive di pandas)
CSV_TITLE_COL = "TITLE"  # Nama kolom untuk Title (Opsional)
