import pytest
import sqlite3
from unittest.mock import patch
from app import create_app
from config import Config

def test_database_connection_error(client, seed_db):
    # Mock database connection to fail
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.Error('Connection failed')
        
        # Test various endpoints
        response = client.get('/api/words')
        assert response.status_code == 500
        assert 'Database error' in response.get_json()['error']
        
        response = client.get('/api/groups')
        assert response.status_code == 500
        assert 'Database error' in response.get_json()['error']

def test_database_constraint_violation(client, seed_db):
    # Try to violate foreign key constraint
    response = client.post('/api/study_sessions', json={
        'group_id': 999,  # Non-existent group
        'activity_id': 1
    })
    assert response.status_code == 400
    assert 'Invalid group ID' in response.get_json()['error']
    
    # Try to violate unique constraint
    response = client.post('/api/words', json={
        'spanish': 'hola',  # Already exists
        'pronunciation': 'test',
        'english': 'test'
    })
    assert response.status_code == 400
    assert 'Word already exists' in response.get_json()['error']

def test_database_concurrent_access(client, seed_db):
    # Simulate concurrent access issues
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.OperationalError('database is locked')
        
        response = client.post('/api/words', json={
            'spanish': 'test',
            'pronunciation': 'test',
            'english': 'test'
        })
        assert response.status_code == 500
        assert 'Database is busy' in response.get_json()['error']

def test_database_transaction_rollback(client, seed_db):
    # Test transaction rollback on error
    with patch('sqlite3.Connection.commit') as mock_commit:
        mock_commit.side_effect = sqlite3.Error('Commit failed')
        
        response = client.post('/api/words', json={
            'spanish': 'test',
            'pronunciation': 'test',
            'english': 'test'
        })
        assert response.status_code == 500
        
        # Verify word wasn't added
        response = client.get('/api/words/search?q=test')
        assert len(response.get_json()['items']) == 0

def test_database_invalid_query(client, seed_db):
    # Test handling of invalid SQL
    with patch('sqlite3.Cursor.execute') as mock_execute:
        mock_execute.side_effect = sqlite3.Error('Invalid SQL')
        
        response = client.get('/api/words')
        assert response.status_code == 500
        assert 'Database error' in response.get_json()['error']

def test_database_data_integrity(client, seed_db):
    # Test handling of corrupted data
    conn = sqlite3.connect(TestConfig.SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Corrupt words_count
    cursor.execute("UPDATE groups SET words_count = -1 WHERE id = 1")
    conn.commit()
    conn.close()
    
    response = client.get('/api/groups')
    assert response.status_code == 200
    groups = response.get_json()['items']
    assert all(g['words_count'] >= 0 for g in groups)  # Should handle negative count 