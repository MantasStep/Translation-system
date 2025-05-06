import os

class Config:
    SECRET_KEY       = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # LLM, DeepL keys, etc.
    BASE_DIR = os.path.dirname(__file__)
    DB_PATH  = os.path.join(BASE_DIR, "db.sqlite3")