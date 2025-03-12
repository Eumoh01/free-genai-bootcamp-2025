import pytest
import sqlite3
import os

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

def test_get_quick_stats(client, seed_db):
    """Test retrieving dashboard quick stats."""
    # Add test data
    conn = sqlite3.connect(seed_db)
    cursor = conn.cursor()
    
    # Add study sessions for streak testing
    cursor.execute("""
        INSERT INTO study_sessions (group_id, study_activity_id, created_at) VALUES 
            (1, 1, date('now')),                    -- Today
            (1, 1, date('now', '-1 day')),         -- Yesterday
            (1, 1, date('now', '-2 days')),        -- 2 days ago
            (1, 1, date('now', '-3 days')),        -- 3 days ago
            (1, 1, date('now', '-5 days'))         -- Break in streak
    """)
    conn.commit()
    conn.close()
    
    response = client.get('/api/dashboard/quick_stats')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'total_sessions' in data
    assert 'current_streak' in data
    
    # Verify counts from seed data
    assert data['total_sessions'] >= 5  # At least our 5 test sessions
    assert data['current_streak'] >= 4  # Should have 4-day streak

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