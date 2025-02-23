import pytest
from app import create_app
from config import Config
import sqlite3
import os

@pytest.fixture
def client():
    # Use test config/database
    test_config = Config()
    test_config.SQLITE_DB_PATH = 'test_words.db'
    
    app = create_app(test_config)
    
    with app.test_client() as client:
        # Set up test database
        conn = sqlite3.connect('test_words.db')
        cursor = conn.cursor()
        
        # Create all necessary tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                spanish TEXT NOT NULL,
                pronunciation TEXT NOT NULL,
                english TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                words_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS word_groups (
                id INTEGER PRIMARY KEY,
                word_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY,
                created_at DATETIME NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS word_review_items (
                id INTEGER PRIMARY KEY,
                word_id INTEGER NOT NULL,
                study_session_id INTEGER NOT NULL,
                correct BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL
            );
        """)
        
        # Add test data
        cursor.executescript("""
            INSERT INTO words (spanish, pronunciation, english) 
            VALUES ('hola', 'OH-lah', 'hello');
            
            INSERT INTO groups (name, words_count) 
            VALUES ('Test Group', 1);
            
            INSERT INTO word_groups (word_id, group_id)
            VALUES (1, 1);
            
            INSERT INTO study_sessions (created_at)
            VALUES (datetime('now'));
            
            INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
            VALUES (1, 1, true, datetime('now'));
        """)
        
        conn.commit()
        conn.close()
        
        yield client
        
        # Clean up
        os.remove('test_words.db')

def test_reset_history(client, seed_db):
    """Test resetting study history.
    
    Verifies:
    - Study sessions are cleared
    - Word reviews are cleared
    - Words and groups remain intact
    - Returns success response
    """
    # Verify initial state from seed data
    conn = sqlite3.connect(TestConfig.SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM study_sessions")
    assert cursor.fetchone()['count'] == 2
    
    cursor.execute("SELECT COUNT(*) as count FROM word_review_items")
    assert cursor.fetchone()['count'] == 3
    
    conn.close()
    
    # Test reset
    response = client.post('/api/reset_history')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Verify reset
    conn = sqlite3.connect(TestConfig.SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM study_sessions")
    assert cursor.fetchone()['count'] == 0
    
    cursor.execute("SELECT COUNT(*) as count FROM word_review_items")
    assert cursor.fetchone()['count'] == 0
    
    # Words and groups should remain
    cursor.execute("SELECT COUNT(*) as count FROM words")
    assert cursor.fetchone()['count'] == 3
    
    cursor.execute("SELECT COUNT(*) as count FROM groups")
    assert cursor.fetchone()['count'] == 2
    
    conn.close()

def test_full_reset(client, seed_db):
    """Test complete database reset.
    
    Verifies:
    - All tables are cleared
    - Database structure remains intact
    - Returns success response
    """
    response = client.post('/api/full_reset')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Verify all tables are empty
    conn = sqlite3.connect(TestConfig.SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    tables = ['words', 'groups', 'word_groups', 'study_sessions', 'word_review_items']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        assert cursor.fetchone()['count'] == 0
    
    conn.close() 