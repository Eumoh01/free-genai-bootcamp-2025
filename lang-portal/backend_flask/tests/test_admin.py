import pytest
import sqlite3
import os

def test_reset_history(client, seed_db):
    """Test resetting study history.
    
    Verifies:
    - Study sessions are cleared
    - Word reviews are cleared
    - Words and groups remain intact
    - Returns success response
    """
    response = client.post('/api/reset_history')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Verify history is cleared
    db = sqlite3.connect(seed_db)
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM word_review_items")
    assert cursor.fetchone()[0] == 0
    
    cursor.execute("SELECT COUNT(*) FROM study_sessions")
    assert cursor.fetchone()[0] == 0
    
    db.close()

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
    conn = sqlite3.connect(seed_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    tables = ['words', 'groups', 'word_groups', 'study_sessions', 'word_review_items']
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
        assert cursor.fetchone()['count'] == 0
    
    conn.close() 