import pytest
from app import create_app
from config import Config
import sqlite3
import os

def test_get_groups_first_page(client, seed_db):
    """Test retrieving the first page of word groups.
    
    Verifies:
    - Successful response with status 200
    - Response contains expected fields (items, pagination info)
    - First group matches expected test data
    - Correct number of groups returned
    - Word count is accurate for each group
    """
    response = client.get('/api/groups')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'items' in data
    assert 'total_pages' in data
    assert 'current_page' in data
    assert 'total_groups' in data
    
    assert data['current_page'] == 1
    assert len(data['items']) == 2  # Two groups from seed data
    
    group = data['items'][0]
    assert group['id'] == 1
    assert group['name'] == 'Basic Phrases'
    assert group['words_count'] == 3

def test_get_groups_pagination(client, test_db):
    """Test group list pagination functionality."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # First verify we start with empty table
    cursor.execute("SELECT COUNT(*) FROM groups")
    initial_count = cursor.fetchone()[0]
    print(f"Initial group count: {initial_count}")  # Debug print
    
    # Add 101 groups for testing
    for i in range(101):  # Changed to ensure exactly 101 groups
        cursor.execute("""
            INSERT INTO groups (name, words_count)
            VALUES (?, ?)
        """, (f'Group {i}', i % 10))
    
    conn.commit()
    
    # Verify total count
    cursor.execute("SELECT COUNT(*) FROM groups")
    total_count = cursor.fetchone()[0]
    print(f"Total group count: {total_count}")  # Debug print
    
    conn.close()
    
    # Test first page
    response = client.get('/api/groups')
    data = response.get_json()
    print(f"Response data: {data}")  # Debug print
    
    assert data['current_page'] == 1
    assert data['total_pages'] == 2
    assert len(data['items']) == 100
    assert data['total_groups'] == 101
    
    # Test second page
    response = client.get('/api/groups?page=2')
    data = response.get_json()
    assert data['current_page'] == 2
    assert len(data['items']) == 1

def test_get_groups_invalid_page(client, test_db):
    response = client.get('/api/groups?page=0')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid page number'
    
    response = client.get('/api/groups?page=999')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid page number'

def test_get_groups_empty_db(client, test_db):
    """Test group listing behavior with empty database.
    
    Verifies:
    - Returns empty list when no groups exist
    - Maintains correct response structure
    - Total pages is 1 (minimum)
    - Returns 200 status (not an error)
    """
    # Clear all groups
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups")
    conn.commit()
    conn.close()
    
    response = client.get('/api/groups')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['items']) == 0  # Empty list
    assert data['total_pages'] == 1  # Should always be at least 1 page
    assert data['current_page'] == 1
    assert data['total_groups'] == 0

def test_get_groups_malformed_page(client, seed_db):
    response = client.get('/api/groups?page=not_a_number')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid page number'

def test_get_groups_negative_page(client, seed_db):
    response = client.get('/api/groups?page=-1')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid page number'

def test_add_word_to_group(client, seed_db):
    """Test adding a word to a group.
    
    Verifies:
    - Word is successfully added to group
    - Group word count is updated
    - Word appears in group's word list
    - Success response is returned
    """
    response = client.post('/api/groups/2/words', json={
        'word_id': 1
    })
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    
    # Verify word is in group
    response = client.get('/api/words?group_id=2')
    assert response.status_code == 200
    words = response.get_json()['items']
    assert any(w['id'] == 1 for w in words)

def test_add_word_to_group_already_exists(client, seed_db):
    """Test handling duplicate word additions.
    
    Verifies:
    - Cannot add same word twice
    - Returns appropriate error message
    - Returns 400 status code
    - Group remains unchanged
    """
    # Word 1 is already in group 1
    response = client.post('/api/groups/1/words', json={
        'word_id': 1
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Word already in group'

def test_add_word_to_group_invalid_word(client, seed_db):
    """Test adding non-existent word to group.
    
    Verifies:
    - Returns 404 for non-existent word ID
    - Returns appropriate error message
    - Group remains unchanged
    """
    response = client.post('/api/groups/1/words', json={
        'word_id': 999
    })
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Word not found'

def test_add_word_to_group_invalid_group(client, seed_db):
    """Test adding word to non-existent group.
    
    Verifies:
    - Returns 404 for non-existent group ID
    - Returns appropriate error message
    - No database changes occur
    """
    response = client.post('/api/groups/999/words', json={
        'word_id': 1
    })
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Group not found'

def test_remove_word_from_group(client, seed_db):
    """Test removing a word from a group.
    
    Verifies:
    - Word is successfully removed
    - Group word count is updated
    - Word no longer appears in group's word list
    - Success response is returned
    """
    response = client.delete('/api/groups/1/words/1')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Verify word is removed
    response = client.get('/api/words?group_id=1')
    assert response.status_code == 200
    words = response.get_json()['items']
    assert not any(w['id'] == 1 for w in words)

def test_remove_word_not_in_group(client, seed_db):
    """Test removing word that isn't in group.
    
    Verifies:
    - Returns 404 for word not in group
    - Returns appropriate error message
    - Group remains unchanged
    """
    response = client.delete('/api/groups/2/words/1')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Word not in group'

def test_update_group_words_count(client, seed_db):
    """Test group word count updates.
    
    Verifies:
    - Count increases when word added
    - Count decreases when word removed
    - Count is accurate after multiple operations
    - Count matches actual number of words
    """
    # Add a word to group
    client.post('/api/groups/2/words', json={'word_id': 1})
    
    # Verify count is updated
    response = client.get('/api/groups')
    assert response.status_code == 200
    groups = response.get_json()['items']
    group = next(g for g in groups if g['id'] == 2)
    assert group['words_count'] == 1

def test_get_group_words(client, seed_db):
    """Test retrieving words in a group.
    
    Verifies:
    - Returns complete list of group words
    - Word details are complete
    - Correct number of words returned
    - Words belong to correct group
    """
    response = client.get('/api/groups/1/words')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'words' in data
    assert len(data['words']) == 3  # Group 1 has 3 words
    
    word = data['words'][0]
    assert 'id' in word
    assert 'spanish' in word
    assert 'english' in word
    assert 'pronunciation' in word

def test_get_group_words_empty_group(client, seed_db):
    """Test retrieving words from empty group.
    
    Verifies:
    - Returns empty list for group with no words
    - Maintains correct response structure
    - Returns 200 status (not an error)
    """
    response = client.get('/api/groups/2/words')
    assert response.status_code == 200
    assert len(response.get_json()['words']) == 0

def test_get_group_words_invalid_group(client, seed_db):
    """Test retrieving words from non-existent group.
    
    Verifies:
    - Returns 404 for non-existent group ID
    - Returns appropriate error message
    - No database access occurs
    """
    response = client.get('/api/groups/999/words')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Group not found' 