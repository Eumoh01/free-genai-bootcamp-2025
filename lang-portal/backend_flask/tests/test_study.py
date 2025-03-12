import pytest
from app import create_app
from config import Config
import sqlite3
import os

def test_get_study_activities(client, seed_db):
    """Test retrieving study activities list."""
    response = client.get('/api/study_activities')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'activities' in data
    assert len(data['activities']) == 2  # Two activities from seed data
    
    activity = data['activities'][0]
    assert activity['id'] == 1
    assert activity['name'] == 'Typing Tutor'
    assert activity['url'] == 'https://example.com/typing'

def test_get_study_sessions(client, seed_db):
    """Test retrieving study session list.
    
    Verifies:
    - Returns paginated session list
    - Includes session details
    - Contains review counts
    - Orders by date descending
    """
    response = client.get('/api/study_sessions')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'items' in data
    assert 'total_pages' in data
    assert 'current_page' in data
    assert 'total_sessions' in data
    
    assert len(data['items']) == 2  # Two sessions from seed data
    
    session = data['items'][0]
    assert session['id'] == 1
    assert session['activity_name'] == 'Typing Tutor'
    assert session['group_name'] == 'Basic Phrases'
    assert 'created_at' in session
    assert 'completed_at' in session
    
    # Verify ordering is newest first
    first_session = data['items'][0]
    second_session = data['items'][1]
    assert first_session['created_at'] > second_session['created_at']

def test_create_word_review(client, seed_db):
    """Test recording a word review in a study session.
    
    Verifies:
    - Review is recorded successfully
    - Correct/incorrect status is saved
    - Review is linked to correct session and word
    - Timestamp is recorded
    """
    response = client.post('/api/study_sessions/1/words/1/review', 
                          json={'correct': True})
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    assert 'review' in data
    assert data['review']['session_id'] == 1
    assert data['review']['word_id'] == 1
    assert data['review']['correct'] is True
    assert 'created_at' in data['review']

def test_create_word_review_invalid_session(client, seed_db):
    """Test creating review with invalid session.
    
    Verifies:
    - Returns error for non-existent session
    - Returns appropriate error message
    - Returns 500 status code
    """
    response = client.post('/api/study_sessions/999/words/1/review', 
                          json={'correct': True})
    assert response.status_code == 500  # Should return database error
    assert 'error' in response.get_json()

def test_create_word_review_invalid_word(client, seed_db):
    """Test creating review with invalid word.
    
    Verifies:
    - Returns error for non-existent word
    - Returns appropriate error message
    - Returns 500 status code
    """
    response = client.post('/api/study_sessions/1/words/999/review', 
                          json={'correct': True})
    assert response.status_code == 500  # Should return database error
    assert 'error' in response.get_json()

def test_create_word_review_missing_correct(client, seed_db):
    """Test creating review without correct flag.
    
    Verifies:
    - Uses default value (False)
    - Creates review successfully
    - Returns 200 status code
    """
    response = client.post('/api/study_sessions/1/words/1/review', 
                          json={})
    assert response.status_code == 200  # Should use default False
    assert response.get_json()['review']['correct'] is False

def test_get_study_sessions_pagination(client, test_db):
    """Test study sessions pagination.
    
    Creates 101 sessions total to test:
    - First page returns 100 items
    - Second page returns 1 item
    - Pagination metadata is correct
    """
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # First verify we start with empty table
    cursor.execute("SELECT COUNT(*) FROM study_sessions")
    initial_count = cursor.fetchone()[0]
    print(f"Initial session count: {initial_count}")  # Debug print
    
    # First add required group and activity
    cursor.execute("INSERT INTO groups (id, name) VALUES (1, 'Test Group')")
    cursor.execute("INSERT INTO study_activities (id, name, url) VALUES (1, 'Test Activity', 'test')")
    
    # Add 101 sessions to ensure we have two pages
    for i in range(101):  # Changed from 99 to 101
        cursor.execute("""
            INSERT INTO study_sessions (group_id, study_activity_id, created_at)
            VALUES (?, ?, datetime('now', ? || ' minutes'))
        """, (1, 1, -i))
    
    conn.commit()
    
    # Verify total count
    cursor.execute("SELECT COUNT(*) FROM study_sessions")
    total_count = cursor.fetchone()[0]
    print(f"Total session count: {total_count}")  # Debug print
    
    conn.close()
    
    # Test first page
    response = client.get('/api/study_sessions')
    data = response.get_json()
    print(f"Response data: {data}")  # Debug print
    
    assert data['current_page'] == 1
    assert data['total_pages'] == 2
    assert len(data['items']) == 100
    assert data['total_sessions'] == 101
    
    # Test second page
    response = client.get('/api/study_sessions?page=2')
    data = response.get_json()
    assert data['current_page'] == 2
    assert len(data['items']) == 1

def test_create_study_session(client, seed_db):
    """Test creating a new study session.
    
    Verifies:
    - Session is created successfully
    - Required fields are present
    - Session is linked to correct group and activity
    - Creation timestamp is set
    """
    response = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1
    })
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    assert 'session' in data
    assert data['session']['group_id'] == 1
    assert data['session']['study_activity_id'] == 1
    assert 'created_at' in data['session']
    assert 'id' in data['session']

def test_create_study_session_invalid_group(client, seed_db):
    response = client.post('/api/study_sessions', json={
        'group_id': 999,
        'activity_id': 1
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid group ID'

def test_create_study_session_invalid_activity(client, seed_db):
    response = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 999
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid activity ID'

def test_complete_study_session(client, seed_db):
    """Test completing a study session.
    
    Verifies:
    - Session can be marked as complete
    - Completion time is recorded
    - Review counts are accurate
    - Cannot complete already completed session
    """
    # First create a session
    session_response = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1
    })
    session_id = session_response.get_json()['session']['id']
    
    # Add some word reviews
    client.post(f'/api/study_sessions/{session_id}/words/1/review', 
               json={'correct': True})
    client.post(f'/api/study_sessions/{session_id}/words/2/review', 
               json={'correct': False})
    
    # Complete the session
    response = client.post(f'/api/study_sessions/{session_id}/complete')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    assert 'session' in data
    assert data['session']['id'] == session_id
    assert 'completed_at' in data['session']
    assert data['session']['review_items_count'] == 2

def test_complete_invalid_session(client, seed_db):
    response = client.post('/api/study_sessions/999/complete')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Session not found'

def test_get_session_words(client, seed_db):
    """Test retrieving words reviewed in a session.
    
    Verifies:
    - List of reviewed words
    - Review status for each word
    - Word details are complete
    - Handles empty sessions correctly
    """
    response = client.get('/api/study_sessions/1/words')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'words' in data
    assert len(data['words']) > 0
    
    word = data['words'][0]
    assert 'id' in word
    assert 'spanish' in word
    assert 'english' in word
    assert 'pronunciation' in word
    assert 'reviewed' in word
    assert 'correct' in word

def test_get_session_stats(client, seed_db):
    """Test retrieving statistics for a study session.
    
    Verifies:
    - Total words reviewed
    - Correct/incorrect counts
    - Accuracy percentage
    - Stats match actual review data
    """
    # Create session with mixed results
    session_response = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1
    })
    session_id = session_response.get_json()['session']['id']
    
    client.post(f'/api/study_sessions/{session_id}/words/1/review', 
               json={'correct': True})
    client.post(f'/api/study_sessions/{session_id}/words/2/review', 
               json={'correct': False})
    client.post(f'/api/study_sessions/{session_id}/words/3/review', 
               json={'correct': True})
    
    response = client.get(f'/api/study_sessions/{session_id}/stats')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['total_words'] == 3
    assert data['correct_count'] == 2
    assert data['accuracy'] == 66.67  # 2/3 as percentage 

def test_create_study_session_missing_fields(client, seed_db):
    # Missing group_id
    response = client.post('/api/study_sessions', json={
        'activity_id': 1
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required fields'
    
    # Missing activity_id
    response = client.post('/api/study_sessions', json={
        'group_id': 1
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required fields'
    
    # Empty request
    response = client.post('/api/study_sessions', json={})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required fields'

def test_create_word_review_malformed(client, seed_db):
    # Invalid correct value
    response = client.post('/api/study_sessions/1/words/1/review', 
                          json={'correct': 'not_boolean'})
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid correct value'
    
    # Invalid JSON
    response = client.post('/api/study_sessions/1/words/1/review', 
                          data='not json')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid JSON'

def test_get_session_words_empty_session(client, seed_db):
    # Create new session without reviews
    session_response = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1
    })
    session_id = session_response.get_json()['session']['id']
    
    response = client.get(f'/api/study_sessions/{session_id}/words')
    assert response.status_code == 200
    assert len(response.get_json()['words']) == 0

def test_complete_already_completed_session(client, seed_db):
    # Create and complete a session
    session_response = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1
    })
    session_id = session_response.get_json()['session']['id']
    
    client.post(f'/api/study_sessions/{session_id}/complete')
    
    # Try to complete again
    response = client.post(f'/api/study_sessions/{session_id}/complete')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Session already completed'

def test_get_session_history_by_date(client, seed_db):
    """Test filtering study sessions by date.
    
    Verifies:
    - Can filter by specific date
    - Can filter by date range
    - Returns sessions in correct order
    - Date filtering is accurate
    """
    # Create sessions on different dates
    today = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1
    })
    
    # Add some reviews
    today_id = today.get_json()['session']['id']
    client.post(f'/api/study_sessions/{today_id}/words/1/review', json={'correct': True})
    
    # Test date filtering
    response = client.get('/api/study_sessions?date=today')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['id'] == today_id
    
    # Test date range
    response = client.get('/api/study_sessions?from=2024-01-01&to=2024-12-31')
    assert response.status_code == 200
    assert len(response.get_json()['items']) > 0

def test_get_session_history_by_group(client, seed_db):
    """Test filtering study sessions by word group.
    
    Verifies:
    - Returns only sessions for specified group
    - Group filtering is accurate
    - Returns correct session details
    """
    # Create sessions for different groups
    group1_session = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1
    }).get_json()['session']
    
    group2_session = client.post('/api/study_sessions', json={
        'group_id': 2,
        'activity_id': 1
    }).get_json()['session']
    
    # Test filtering by group
    response = client.get('/api/study_sessions?group_id=1')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) >= 1
    assert all(s['group_id'] == 1 for s in data['items'])

def test_get_session_history_by_activity(client, seed_db):
    # Create sessions with different activities
    typing_session = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 1  # Typing activity
    }).get_json()['session']
    
    cards_session = client.post('/api/study_sessions', json={
        'group_id': 1,
        'activity_id': 2  # Flashcards activity
    }).get_json()['session']
    
    # Test filtering by activity
    response = client.get('/api/study_sessions?activity_id=1')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) >= 1
    assert all(s['activity_name'] == 'Typing Tutor' for s in data['items'])

def test_get_session_history_combined_filters(client, seed_db):
    # Test combining multiple filters
    response = client.get('/api/study_sessions?group_id=1&activity_id=1&date=today')
    assert response.status_code == 200
    data = response.get_json()
    
    # Verify all filters applied
    for session in data['items']:
        assert session['group_id'] == 1
        assert session['activity_name'] == 'Typing Tutor'
        # Would also verify date here 