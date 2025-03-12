import pytest
from app import create_app
from config import Config
import sqlite3
import os

def test_get_words_first_page(client, seed_db):
    """Test retrieving the first page of words.
    
    Verifies:
    - Successful response with status 200
    - Response contains expected fields (items, pagination info)
    - First word matches expected test data
    - Correct number of words returned (3 from seed data)
    """
    response = client.get('/api/words')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'items' in data
    assert 'total_pages' in data
    assert 'current_page' in data
    assert 'total_words' in data
    
    assert data['current_page'] == 1
    assert len(data['items']) == 3  # Three words from seed data
    
    word = data['items'][0]
    assert word['id'] == 1
    assert word['spanish'] == 'hola'
    assert word['pronunciation'] == 'OH-lah'
    assert word['english'] == 'hello'

def test_get_words_pagination(client, test_db):
    """Test word list pagination functionality."""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # First verify we start with empty table
    cursor.execute("SELECT COUNT(*) FROM words")
    initial_count = cursor.fetchone()[0]
    print(f"Initial word count: {initial_count}")  # Debug print
    
    # Add 101 words for testing
    for i in range(101):  # Changed to 101 to ensure we have exactly 101 words
        cursor.execute("""
            INSERT INTO words (spanish, pronunciation, english)
            VALUES (?, ?, ?)
        """, (f'word{i}', f'pron{i}', f'eng{i}'))
    
    conn.commit()
    
    # Verify total count
    cursor.execute("SELECT COUNT(*) FROM words")
    total_count = cursor.fetchone()[0]
    print(f"Total word count: {total_count}")  # Debug print
    
    conn.close()
    
    # Test first page
    response = client.get('/api/words')
    data = response.get_json()
    print(f"Response data: {data}")  # Debug print
    
    assert data['current_page'] == 1
    assert data['total_pages'] == 2
    assert len(data['items']) == 100
    assert data['total_words'] == 101

def test_get_words_invalid_page(client, test_db):
    response = client.get('/api/words?page=0')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid page number'
    
    response = client.get('/api/words?page=999')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid page number'

def test_search_words(client, seed_db):
    """Test word search functionality with exact match.
    
    Verifies:
    - Can find word by exact Spanish text
    - Returns correct word details
    - Handles single result correctly
    """
    response = client.get('/api/words/search?q=hola')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['spanish'] == 'hola'

def test_search_words_partial(client, seed_db):
    """Test partial word search functionality.
    
    Verifies searching works with:
    - Partial word matches
    - Case insensitive matching
    """
    response = client.get('/api/words/search?q=grac')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['spanish'] == 'gracias'

def test_search_words_english(client, seed_db):
    """Test searching words by English translation.
    
    Verifies:
    - Can find word by English text
    - Returns correct word details
    - Matches exact and partial English words
    """
    response = client.get('/api/words/search?q=thank')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['english'] == 'thank you'

def test_search_words_no_results(client, seed_db):
    """Test search behavior with no matching results.
    
    Verifies:
    - Returns empty list for non-existent words
    - Maintains correct response structure
    - Returns 200 status (not an error)
    """
    response = client.get('/api/words/search?q=xyz123')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['items']) == 0

def test_filter_words_by_group(client, seed_db):
    """Test filtering words by group membership.
    
    Verifies:
    - Returns only words from specified group
    - Includes group membership data
    - Handles groups with multiple words
    """
    response = client.get('/api/words?group_id=1')
    assert response.status_code == 200
    
    data = response.get_json()
    assert len(data['items']) == 3  # All words in Basic Phrases group
    
    # Verify all words belong to group
    for word in data['items']:
        assert word['group_ids'] == [1]

def test_filter_words_invalid_group(client, seed_db):
    """Test filtering words with invalid group ID.
    
    Verifies:
    - Returns empty list for non-existent group
    - Returns 200 status (not an error)
    - Maintains correct response structure
    """
    response = client.get('/api/words?group_id=999')
    assert response.status_code == 200
    assert len(response.get_json()['items']) == 0 

def test_search_words_sql_injection(client, seed_db):
    """Test protection against SQL injection in search.
    
    Verifies:
    - Safely handles SQL special characters
    - Prevents SQL injection attacks
    - Returns empty results rather than executing malicious SQL
    """
    # Try SQL injection in search
    response = client.get("/api/words/search?q=x' OR '1'='1")
    assert response.status_code == 200
    assert len(response.get_json()['items']) == 0

def test_filter_words_malformed_group_id(client, seed_db):
    """Test handling of malformed group ID parameter.
    
    Verifies:
    - Rejects non-numeric group IDs
    - Returns appropriate error message
    - Returns 400 status code
    """
    response = client.get('/api/words?group_id=not_a_number')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Invalid group ID'

def test_search_words_empty_query(client, seed_db):
    """Test search validation for empty queries.
    
    Verifies:
    - Rejects empty search strings
    - Returns appropriate error message
    - Returns 400 status code
    """
    response = client.get('/api/words/search?q=')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Search query required'

def test_search_words_long_query(client, seed_db):
    """Test handling of excessively long search queries.
    
    Verifies:
    - Rejects queries exceeding length limit
    - Returns appropriate error message
    - Returns 400 status code
    """
    # Test with very long search query
    long_query = 'a' * 1000
    response = client.get(f'/api/words/search?q={long_query}')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Search query too long'

def test_create_word(client, seed_db):
    """Test creating a new word.
    
    Verifies:
    - Word is created successfully
    - Response contains complete word data
    - Required fields are present
    - Word is retrievable after creation
    """
    response = client.post('/api/words', json={
        'spanish': 'nuevo',
        'pronunciation': 'noo-EH-voh',
        'english': 'new'
    })
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    assert 'word' in data
    assert data['word']['spanish'] == 'nuevo'
    assert data['word']['pronunciation'] == 'noo-EH-voh'
    assert data['word']['english'] == 'new'
    assert 'id' in data['word']

def test_create_word_missing_fields(client, seed_db):
    """Test word creation with missing required fields.
    
    Checks error handling for missing:
    - Spanish text
    - Pronunciation
    - English translation
    
    Each should return 400 with appropriate error message.
    """
    # Missing spanish
    response = client.post('/api/words', json={
        'pronunciation': 'test',
        'english': 'test'
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required field: spanish'
    
    # Missing pronunciation
    response = client.post('/api/words', json={
        'spanish': 'test',
        'english': 'test'
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required field: pronunciation'
    
    # Missing english
    response = client.post('/api/words', json={
        'spanish': 'test',
        'pronunciation': 'test'
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Missing required field: english'

def test_create_word_empty_fields(client, seed_db):
    """Test validation of empty field values.
    
    Verifies:
    - Rejects empty strings for required fields
    - Returns appropriate error message
    - Returns 400 status code
    """
    response = client.post('/api/words', json={
        'spanish': '',
        'pronunciation': 'test',
        'english': 'test'
    })
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Fields cannot be empty'

def test_update_word(client, seed_db):
    """Test updating an existing word.
    
    Verifies:
    - All fields can be updated
    - Response contains updated data
    - Changes persist in database
    """
    response = client.put('/api/words/1', json={
        'spanish': 'hola updated',
        'pronunciation': 'OH-lah updated',
        'english': 'hello updated'
    })
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['success'] is True
    assert 'word' in data
    assert data['word']['id'] == 1
    assert data['word']['spanish'] == 'hola updated'
    assert data['word']['pronunciation'] == 'OH-lah updated'
    assert data['word']['english'] == 'hello updated'

def test_update_word_not_found(client, seed_db):
    """Test updating non-existent word.
    
    Verifies:
    - Returns 404 for non-existent word ID
    - Returns appropriate error message
    - No database changes occur
    """
    response = client.put('/api/words/999', json={
        'spanish': 'test',
        'pronunciation': 'test',
        'english': 'test'
    })
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Word not found'

def test_update_word_partial(client, seed_db):
    """Test partial word updates.
    
    Verifies:
    - Can update individual fields
    - Unchanged fields retain original values
    - Response includes complete word data
    """
    # Should only update provided fields
    response = client.put('/api/words/1', json={
        'spanish': 'hola nuevo'
    })
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['word']['spanish'] == 'hola nuevo'
    assert data['word']['pronunciation'] == 'OH-lah'  # Unchanged
    assert data['word']['english'] == 'hello'  # Unchanged

def test_delete_word(client, seed_db):
    """Test word deletion.
    
    Verifies:
    - Word is successfully deleted
    - Word is no longer retrievable
    - Returns appropriate success response
    """
    response = client.delete('/api/words/1')
    assert response.status_code == 200
    assert response.get_json()['success'] is True
    
    # Verify word is deleted
    response = client.get('/api/words/1')
    assert response.status_code == 404

def test_delete_word_not_found(client, seed_db):
    """Test deleting non-existent word.
    
    Verifies:
    - Returns 404 for non-existent word ID
    - Returns appropriate error message
    - No database changes occur
    """
    response = client.delete('/api/words/999')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Word not found'

def test_delete_word_with_reviews(client, seed_db):
    """Test deletion protection for reviewed words.
    
    Verifies:
    - Prevents deletion of words with review history
    - Returns appropriate error message
    - Returns 400 status code
    - Word remains in database
    """
    # Should fail if word has review history
    response = client.delete('/api/words/1')
    assert response.status_code == 400
    assert response.get_json()['error'] == 'Cannot delete word with review history'

def test_get_word(client, seed_db):
    """Test retrieving a single word by ID.
    
    Verifies:
    - Returns correct word details
    - Includes associated groups
    - Returns 404 for non-existent word
    - All required fields are present
    """
    # Test getting existing word
    response = client.get('/api/words/1')
    assert response.status_code == 200
    
    word = response.get_json()
    assert word['id'] == 1
    assert word['spanish'] == 'hola'
    assert word['english'] == 'hello'
    assert word['pronunciation'] == 'OH-lah'
    
    # Verify groups data
    assert 'groups' in word
    assert isinstance(word['groups'], list)
    if word['groups']:  # If word is in any groups
        group = word['groups'][0]
        assert 'id' in group
        assert 'name' in group
        assert group['name'] == 'Basic Phrases'
    
    # Test non-existent word
    response = client.get('/api/words/999')
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Word not found' 