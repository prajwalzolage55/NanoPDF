import os


class Config:
    # ---------------- Basic Settings ----------------
    SECRET_KEY = "supersecretkey"  # Change in production

    # ---------------- File Upload Settings ----------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "original")
    COMPRESSED_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "compressed")

    ALLOWED_EXTENSIONS = {"pdf"}

    # Maximum upload size (10 MB)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024   # 100 MB

    # ---------------- Compression Settings ----------------
    DEFAULT_COMPRESSION_LEVEL = "medium"
