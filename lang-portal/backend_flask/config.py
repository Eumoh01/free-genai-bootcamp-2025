import os

class Config:
    # Database settings
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SQLITE_DB_PATH = os.path.join(BASE_DIR, 'words.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API settings
    JSON_SORT_KEYS = False
    ITEMS_PER_PAGE = 100
    TESTING = False

class TestConfig(Config):
    SQLITE_DB_PATH = 'test_words.db'
    TESTING = True
