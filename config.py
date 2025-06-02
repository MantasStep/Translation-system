import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BASE_DIR = os.path.dirname(__file__)
    DB_PATH  = os.path.join(BASE_DIR, "db.sqlite3")
    UPLOAD_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\uploads"
    TRANSLATED_FOLDER = r"E:\univerui\4_kursas\bakalauras\Test\Translation-system\instance\translations"
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"txt", "docx"}
    MAX_TEXT_LENGTH = 5000