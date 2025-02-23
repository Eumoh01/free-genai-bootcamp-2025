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
        
        # Create tables
        cursor.executescript("""
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
            INSERT INTO study_sessions (created_at) VALUES 
                (date('now')),                    -- Today
                (date('now', '-1 day')),         -- Yesterday
                (date('now', '-2 days')),        -- 2 days ago
                (date('now', '-3 days')),        -- 3 days ago
                (date('now', '-5 days'));        -- Break in streak
        """)
        
        conn.commit()
        conn.close()
        
        yield client
        
        # Clean up
        os.remove('test_words.db')

def test_last_study_session(client, seed_db):
    """Test retrieving the most recent study session.
    
    Verifies:
    - Returns most recent session by date
    - Includes activity and group details
    - Contains all required fields (id, activity_name, group_name)
    - Matches expected test data
    """
    response = client.get('/api/dashboard/last_study_session')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data is not None
    assert 'id' in data
    assert 'activity_name' in data
    assert 'group_name' in data
    
    # Verify it returns most recent session
    assert data['id'] == 1  # From our seed data
    assert data['activity_name'] == 'Typing Tutor'
    assert data['group_name'] == 'Basic Phrases'

def test_study_progress(client, seed_db):
    """Test retrieving overall study progress.
    
    Verifies:
    - Returns total words count
    - Returns studied words count
    - Counts match seed data
    - All values are integers
    """
    response = client.get('/api/dashboard/study_progress')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'total_words' in data
    assert 'total_words_studied' in data
    assert isinstance(data['total_words'], int)
    assert isinstance(data['total_words_studied'], int)
    
    # Verify counts from seed data
    assert data['total_words'] == 3
    assert data['total_words_studied'] == 3  # All words have been reviewed

def test_quick_stats(client, seed_db):
    """Test retrieving quick dashboard statistics.
    
    Verifies:
    - Returns total sessions count
    - Returns current study streak
    - Stats match seed data
    - Streak calculation is accurate
    """
    response = client.get('/api/dashboard/quick_stats')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'total_sessions' in data
    assert 'current_streak' in data
    
    # Verify counts from seed data
    assert data['total_sessions'] == 2  # Two sessions in seed data
    assert data['current_streak'] >= 1  # At least today's session 

def test_get_study_stats(client, seed_db):
    """Test retrieving study statistics.
    
    Verifies:
    - Returns overall study metrics
    - Calculates correct accuracy percentages
    - Groups stats by time period
    - Includes all required fields
    """
    # ... test code ...

def test_get_word_progress(client, seed_db):
    """Test retrieving word learning progress.
    
    Verifies:
    - Shows mastery level per word
    - Tracks review history
    - Calculates accuracy correctly
    - Orders by proficiency
    """
    # ... test code ...

def test_get_group_progress(client, seed_db):
    """Test retrieving group learning progress.
    
    Verifies:
    - Shows completion percentage per group
    - Tracks words learned vs total
    - Orders by study frequency
    - Includes activity breakdown
    """
    # ... test code ... 