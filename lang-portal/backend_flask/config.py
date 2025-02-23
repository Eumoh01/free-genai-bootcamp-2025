import os

class Config:
    # Database settings
    SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend_flask', 'words.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API settings
    JSON_SORT_KEYS = False
    ITEMS_PER_PAGE = 100
