# Backend Technical Specs

## Business Goal 
A language learning school wants to build a prototype of learning portal which will act as three things:
- Inventory of possible vocabulary that can be learned
- Act as a  Learning record store (LRS), providing correct and wrong score on practice vocabulary
- A unified launchpad to launch different learning apps

## Tech Requirements
- Use Python Flask framework for backend
- Use SQLite for database
- Use Flask-RESTful for API
- API will always return JSON
- Use SQlite3 for database
- There will be no authentification or authorization
- Everything treated as a single user

## Directory Structure

```
backend_flask/
├── app.py                   # Application factory and Flask setup
├── config.py               # Environment configurations
├── tasks.py               # Invoke tasks for db init, migrations, and seeding
├── requirements.txt        # Python dependencies
│
├── lib/                   # Shared utilities and helpers
│   └── [Database utilities, error handling, shared code]
│
├── routes/               # API endpoints organized by feature
│   └── [Dashboard, words, groups, study, admin routes]
│
├── migrations/          # SQL migration files
│   └── [Numbered SQL migration files]
│
├── seeds/              # Seed data in JSON format
│   └── [JSON files with Spanish vocabulary data]
│
└── tests/             # Test suite
    └── [Test files matching route structure]
```

## Database Schema
Single sqlite database called `words.db` that will be in the root of the project folder of `backend_flask`

### Tables
words — Stores individual Spanish vocabulary words.
- id(PK) int - Unique identifier for each word
- spanish string - The word in Spanish
- pronunciation string - Pronunciation guide
- english string - English translation of the word

groups — Manages collections of words.
- id(PK) int - Unique identifier for each group
- name string - Name of the group
- words_count int - Counter cache for number of words in group

word_groups — Join table for words and groups relationship.
- id(PK) int - Unique identifier for each relationship
- word_id(FK) int - References words.id
- group_id(FK) int - References groups.id

study_activities — Defines available study activities.
- id(PK) int - Unique identifier for each activity
- name string - Name of the activity
- url string - Full URL of the study activity
- preview_url string - URL to activity preview image

study_sessions — Records individual study sessions.
- id(PK) int - Unique identifier for each session
- group_id(FK) int - References groups.id
- study_activity_id(FK) int - References study_activities.id
- created_at datetime - When session was created

word_review_items — Tracks individual word reviews.
- id(PK) int - Unique identifier for each review
- word_id(FK) int - References words.id
- study_session_id(FK) int - References study_sessions.id
- correct boolean - Whether answer was correct
- created_at datetime - When review occurred

## API Endpoints:

### GET /api/dashboard/last_study_session
Returns details of the most recent study session
#### Response:
```json
{
  "id": 123,
  "activity_id": 1,
  "activiy_name": "Typing Tutor",
  "group_id": 1,
  "group_name": "Core Verbs",
  "created_at": "2024-03-15T14:30:00Z"
}
```

### GET /api/dashboard/study_progress
Returns overall learning progress statistics
#### Response:
```json
{
  "total_words": 500,
  "total_words_studied": 150
}
```

### GET /api/dashboard/quick_stats
Returns summary statistics for study performance
#### Response:
```json
{
  "total_sessions": 45,
  "current_streak": 5
}
```

### GET /api/words
Returns list of vocabulary words with pagination (100 items per page)
#### Response:
```json
{
  "items": [
    {
      "id": 1,
      "spanish": "hablar",
      "pronunciation": "ah-BLAR",
      "english": "to speak"
    }
  ],
  "total_pages": 5,
  "current_page": 1,
  "total_words": 500
}
```

### GET /api/groups
Returns list of word groups with pagination (100 items per page)
#### Response:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Core Verbs",
      "words_count": 50
    }
  ],
  "total_pages": 3,
  "current_page": 1,
  "total_groups": 250
}
```

### GET /api/study_activities
Returns list of available study activities
#### Response:
```json
{
  "activities": [
    {
      "id": 1,
      "name": "Typing Tutor",
      "url": "https://www.typingtutor.com",
      "preview_url": "https://www.typingtutor.com/preview.jpg"
    }
  ]
}
```

### GET /api/study_sessions
Returns list of study sessions with pagination (100 items per page)
#### Response:
```json
{
  "items": [
    {
      "id": 123,
      "activity_name": "Typing Tutor",
      "group_name": "Core Verbs",
      "start_time": "2024-03-15T14:30:00Z",
      "end_time": "2024-03-15T14:45:00Z",
      "review_items_count": 20
    }
  ],
  "total_pages": 3,
  "current_page": 1,
  "total_sessions": 250
}
```

### POST /api/reset_history
Resets all study history data
#### Response:
```json
{
  "message": "Study history has been reset",
  "success": true
}
```

### POST /api/full_reset
Resets entire database to initial state
#### Response:
```json
{
  "message": "Database has been reset to initial state",
  "success": true
}
```

### POST /api/study_sessions/:id/words/:word_id/review
Records a word review result
#### Request Params:
- id (int): Study session ID
- word_id (int): Word ID
- correct (boolean): Whether the answer was correct or not
#### Request Payload:
```json
{
  "correct": true
}
```
#### Response:
```json
{
  "message": "Word review recorded successfully",
  "success": true,
  "review": {
    "session_id": 123,
    "word_id": 456,
    "correct": true,
    "created_at": "2024-03-15T14:45:00Z"
  }
}
```

## Added API Endpoints

### Words
- `GET /api/words/<id>` - Get a single word with its group associations
  - Response: Word details including spanish, english, pronunciation, and groups
  - Error: 404 if word not found

### Groups
- `GET /api/groups/<id>/words` - Get all words in a group
  - Response: List of words with details
  - Error: 404 if group not found

### Study Sessions
- `POST /api/study_sessions/<id>/words/<word_id>/review` - Record word review
  - Request: `{ "correct": boolean }`
  - Response: Review details with timestamp
  - Error: 400 for invalid input, 500 for database errors

- `GET /api/study_sessions/<id>/words` - Get words reviewed in session
  - Response: List of words with review status
  - Error: 404 if session not found

- `GET /api/study_sessions/<id>/stats` - Get session statistics
  - Response: Total words, correct count, accuracy percentage
  - Error: 404 if session not found

- `POST /api/study_sessions/<id>/complete` - Complete a study session
  - Response: Updated session details
  - Error: 400 if already completed, 404 if not found

## Invoke Tasks 
Invoke is a task runner that will be used to run the tasks needed for the Lang Portal
List out possible tasks needed for the Lang Portal

### Initialize Database
This task will initialize the sqlite database called `words.db`

### Migrate Database
This task will run migrations sql files on the database

Migrations will be in the `migrations` folder
The migration files will be run in order of their file name
The file names should look like this:

```sql
001_init.sql
002_create_words_table.sql
003_create_groups_table.sql
004_create_word_groups_table.sql
005_create_study_activities_table.sql
006_create_study_sessions_table.sql
007_create_word_review_items_table.sql
```

### Seed Data 
This task will import json files and transform them into target data for our database

All seed files will be in the `seeds` folder

In our task we should have a DSL to specify each seed file and its expected group word name

```json
[
  {
    "spanish": "hola",
    "english": "hello",
    "pronunciation": "oh-lah",
  },
  {
    "spanish": "adios",
    "english": "goodbye",
    "pronunciation": "ah-dyohs",
  }
]
```



## Possible Future API Endpoints(not implemented):

GET /api/dashboard/last_study_session - Returns details of the most recent study session

GET /api/dashboard/study_progress - Returns overall learning progress statistics

GET /api/dashboard/quick_stats - Returns summary statistics for study performance


GET /api/study_activities/:id - Returns details for a specific study activity

GET /api/study_activities/:id/study_sessions - Returns study sessions for a specific activity

POST /api/study_activities - Creates a new study session
- Required params: group_id, study_activity_id


GET /api/words/:id - Returns details for a specific word


GET /api/groups/:id - Returns details for a specific group

GET /api/groups/:id/words - Returns all words belonging to a specific group

GET /api/groups/:id/study_sessions - Returns study sessions for a specific group



GET /api/study_sessions/:id - Returns details for a specific study session

GET /api/study_sessions/:id/words - Returns words reviewed in a specific study session








