# Language Portal API Documentation

## Overview
The Language Portal API provides endpoints for managing vocabulary words, word groups, and study sessions. The API follows REST principles and returns JSON responses.

## Common Response Format
All responses follow this general structure:
```json
{
    "success": true,
    "data": {}, // Response data varies by endpoint
    "error": null // Present only on error
}
```

## Endpoints

### Words

#### GET /api/words
Get paginated list of vocabulary words.

Query Parameters:
- `page`: Page number (default: 1)
- `group_id`: Filter by group ID
- `q`: Search query

Response:
```json
{
    "items": [
        {
            "id": 1,
            "spanish": "hola",
            "english": "hello",
            "pronunciation": "OH-lah",
            "group_ids": [1, 2]
        }
    ],
    "total_pages": 10,
    "current_page": 1,
    "total_words": 100
}
```

#### POST /api/words
Create a new vocabulary word.

Request Body:
```json
{
    "spanish": "nuevo",
    "english": "new",
    "pronunciation": "noo-EH-voh"
}
```

### Groups

#### GET /api/groups
Get paginated list of word groups.

Query Parameters:
- `page`: Page number (default: 1)

Response:
```json
{
    "items": [
        {
            "id": 1,
            "name": "Basic Phrases",
            "words_count": 10
        }
    ],
    "total_pages": 5,
    "current_page": 1
}
```

### Study Sessions

#### POST /api/study_sessions
Create a new study session.

Request Body:
```json
{
    "group_id": 1,
    "activity_id": 1
}
```

#### POST /api/study_sessions/{session_id}/words/{word_id}/review
Record a word review in a study session.

Request Body:
```json
{
    "correct": true
}
```

### Admin Operations

#### POST /api/reset_history
Reset all study history.

Response:
```json
{
    "success": true,
    "message": "Study history cleared"
}
```

#### POST /api/full_reset
Reset entire database.

Response:
```json
{
    "success": true,
    "message": "Database reset complete"
}
```

#### POST /api/import
Import vocabulary data.

Request Body:
```json
{
    "words": [
        {
            "spanish": "nuevo",
            "english": "new",
            "pronunciation": "noo-EH-voh"
        }
    ]
}
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Server Error

Error responses include a message:
```json
{
    "success": false,
    "error": "Detailed error message"
}
``` 