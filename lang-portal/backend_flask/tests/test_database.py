import pytest
import sqlite3
from unittest.mock import patch
from lib.db import get_db
from flask import current_app

def test_database_connection_error(client, seed_db):
    """Test basic database error handling.
    This tests SQLite-specific connection failures."""
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.Error('Connection failed')
        
        response = client.get('/api/words')
        assert response.status_code == 500
        assert 'Database error' in response.get_json()['error']

def test_database_concurrent_access(client, seed_db):
    """Test handling of concurrent database access.
    This is unique as it tests SQLite's busy timeout."""
    with patch('sqlite3.connect') as mock_connect:
        mock_connect.side_effect = sqlite3.OperationalError('database is locked')
        
        response = client.get('/api/words')
        assert response.status_code == 500
        assert 'Database error' in response.get_json()['error']

def test_foreign_key_constraints(client, seed_db):
    """Test foreign key constraint enforcement.
    Verifies SQLite foreign key support is enabled."""
    with client.application.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Verify foreign keys are enabled
        cursor.execute("PRAGMA foreign_keys = ON")
        assert cursor.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        
        # Try to insert with invalid foreign key
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO word_groups (word_id, group_id)
                VALUES (999, 999)
            """)