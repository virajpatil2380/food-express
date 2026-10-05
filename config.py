import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    # Database Settings
    DB_ENGINE = os.getenv("DB_ENGINE", "mysql")  # 'mysql' or 'sqlite'
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "food_delivery_db")
    
    # SQLite Fallback Path
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "food_delivery.db")
    
    # Flask Server Settings
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000/api")
