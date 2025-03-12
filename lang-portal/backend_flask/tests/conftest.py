import pytest
from app import create_app
from config import TestConfig
import sqlite3
import os

@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app, test_db):
    """Create a test client with test database"""
    return app.test_client()

@pytest.fixture
def test_db():
    """Creates a test database with required tables.
    
    Returns:
        str: Path to the test database file
        
    Note:
        The database is automatically deleted after each test.
    """
    db_path = TestConfig.SQLITE_DB_PATH
    
    # Remove existing test database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create fresh database and tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create all required tables
    cursor.executescript("""
        -- Words table stores vocabulary items
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Changed to AUTOINCREMENT
            spanish TEXT NOT NULL,
            pronunciation TEXT NOT NULL,
            english TEXT NOT NULL
        );
        
        -- Groups organize words into categories
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Changed to AUTOINCREMENT
            name TEXT NOT NULL,
            words_count INTEGER DEFAULT 0
        );
        
        -- Word-group relationships
        CREATE TABLE IF NOT EXISTS word_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Changed to AUTOINCREMENT
            word_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            FOREIGN KEY (word_id) REFERENCES words(id),
            FOREIGN KEY (group_id) REFERENCES groups(id)
        );
        
        -- Study activities define different learning methods
        CREATE TABLE IF NOT EXISTS study_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Changed to AUTOINCREMENT
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            preview_url TEXT
        );
        
        -- Study sessions track learning progress
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Changed to AUTOINCREMENT
            group_id INTEGER NOT NULL,
            study_activity_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            completed_at DATETIME,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
        );
        
        -- Word reviews track performance in study sessions
        CREATE TABLE IF NOT EXISTS word_review_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Changed to AUTOINCREMENT
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
    
    # Clean up - remove test database after test completes
    if os.path.exists(db_path):
        os.remove(db_path)

@pytest.fixture
def seed_db(test_db):
    """Populates the test database with sample data.
    
    Args:
        test_db: The test database fixture
        
    Returns:
        str: Path to the seeded test database
    """
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Add sample data without specifying IDs (let SQLite auto-increment)
    cursor.executescript("""
        INSERT INTO words (spanish, pronunciation, english) VALUES 
            ('hola', 'OH-lah', 'hello'),
            ('gracias', 'GRAH-see-ahs', 'thank you'),
            ('por favor', 'por fah-VOR', 'please');
            
        INSERT INTO groups (name) VALUES
            ('Basic Phrases'),
            ('Numbers');
            
        INSERT INTO study_activities (name, url) VALUES 
            ('Typing Tutor', 'https://example.com/typing'),
            ('Flashcards', 'https://example.com/cards');
    """)
    
    # Get the auto-generated IDs
    cursor.execute("SELECT id FROM words ORDER BY id")
    word_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM groups WHERE name='Basic Phrases'")
    group_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM study_activities")
    activity_ids = [row[0] for row in cursor.fetchall()]
    
    # Use the actual IDs for relationships
    for word_id in word_ids:
        cursor.execute("INSERT INTO word_groups (word_id, group_id) VALUES (?, ?)",
                      (word_id, group_id))
                
    # Create study sessions - now create two sessions as expected by test
    cursor.execute("""
        INSERT INTO study_sessions (group_id, study_activity_id, created_at)
        VALUES 
            (?, ?, datetime('now')),
            (?, ?, datetime('now', '-1 day'))
    """, (group_id, activity_ids[0], group_id, activity_ids[1]))
    
    # Get the session IDs
    cursor.execute("SELECT id FROM study_sessions ORDER BY created_at DESC")
    session_ids = [row[0] for row in cursor.fetchall()]
    
    # Add word reviews for both sessions
    for session_id in session_ids:
        for word_id in word_ids:
            cursor.execute("""
                INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (word_id, session_id, True))
    
    # Update group word count
    cursor.execute("UPDATE groups SET words_count = ? WHERE id = ?",
                  (len(word_ids), group_id))
    
    conn.commit()
    conn.close()
    
    return test_db 