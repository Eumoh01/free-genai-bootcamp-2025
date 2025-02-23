import pytest
from app import create_app
from config import Config
import sqlite3
import os

class TestConfig(Config):
    SQLITE_DB_PATH = 'test_words.db'
    TESTING = True

@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

@pytest.fixture
def test_db():
    """Creates a test database with required tables.
    
    Returns:
        str: Path to the test database file
        
    Note:
        The database is automatically deleted after each test.
    """
    db_path = 'test_words.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create all required tables
    cursor.executescript("""
        -- Words table stores vocabulary items
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            spanish TEXT NOT NULL,
            pronunciation TEXT NOT NULL,
            english TEXT NOT NULL
        );
        
        -- Groups organize words into categories
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            words_count INTEGER DEFAULT 0
        );
        
        -- Word-group relationships
        CREATE TABLE IF NOT EXISTS word_groups (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            FOREIGN KEY (word_id) REFERENCES words(id),
            FOREIGN KEY (group_id) REFERENCES groups(id)
        );
        
        -- Study activities define different learning methods
        CREATE TABLE IF NOT EXISTS study_activities (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            preview_url TEXT
        );
        
        -- Study sessions track learning progress
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY,
            group_id INTEGER NOT NULL,
            study_activity_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            completed_at DATETIME,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
        );
        
        -- Word reviews track performance in study sessions
        CREATE TABLE IF NOT EXISTS word_review_items (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL,
            study_session_id INTEGER NOT NULL,
            correct BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (word_id) REFERENCES words(id),
            FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
        );
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def seed_db(test_db):
    """Populates the test database with sample data.
    
    The sample data includes:
    - Basic vocabulary words
    - Word groups (Basic Phrases, Numbers)
    - Study activities (Typing Tutor, Flashcards)
    - Sample study sessions with word reviews
    
    Args:
        test_db: The test database fixture
        
    Returns:
        str: Path to the seeded test database
    """
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Add sample words
    cursor.executescript("""
        INSERT INTO words (id, spanish, pronunciation, english) VALUES 
            (1, 'hola', 'OH-lah', 'hello'),
            (2, 'gracias', 'GRAH-see-ahs', 'thank you'),
            (3, 'por favor', 'por fah-VOR', 'please');
            
        INSERT INTO groups (id, name) VALUES
            (1, 'Basic Phrases'),
            (2, 'Numbers');
            
        INSERT INTO word_groups (word_id, group_id) VALUES
            (1, 1),
            (2, 1),
            (3, 1);
            
        INSERT INTO study_activities (id, name, url) VALUES 
            (1, 'Typing Tutor', 'https://example.com/typing'),
            (2, 'Flashcards', 'https://example.com/cards');
            
        INSERT INTO study_sessions (id, group_id, study_activity_id, created_at) VALUES
            (1, 1, 1, datetime('now')),
            (2, 1, 2, datetime('now', '-1 day'));
            
        INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES
            (1, 1, 1, datetime('now')),
            (2, 1, 0, datetime('now')),
            (3, 2, 1, datetime('now', '-1 day'));
            
        UPDATE groups SET words_count = 3 WHERE id = 1;
    """)
    
    conn.commit()
    conn.close()
    
    return test_db 