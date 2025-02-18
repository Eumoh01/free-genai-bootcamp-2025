# Backend Technical Specs

## Business Goal: 
A language learning school wants to build a prototype of learning portal which will act as three things:
- Inventory of possible vocabulary that can be learned
- Act as a  Learning record store (LRS), providing correct and wrong score on practice vocabulary
- A unified launchpad to launch different learning apps

## Tech Requirements:
- Use Python Flask framework for backend
- Use SQLite for database
- Use Flask-RESTful for API
- API will always return JSON
- Use SQlite3 for database
- There will be no authentification or authorization
- Everything treated as a single user

## Database Schema:
words — Stores individual Spanish vocabulary words.
- id(PK) int - Unique identifier for each word
- spanish string - The word in Spanish
- pronunciation string - Pronunciation guide
- english string - English translation of the word
- parts json - Word components stored in JSON format

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

GET /api/dashboard/last_study_session - Returns details of the most recent study session

GET /api/dashboard/study_progress - Returns overall learning progress statistics

GET /api/dashboard/quick_stats - Returns summary statistics for study performance

GET /api/words - Returns list of vocabulary words
- Pagination with 100 items per page

GET /api/groups - Returns list of word groups
- Pagination with 100 items per page

GET /api/study_activities - Returns list of study activities

GET /api/study_sessions - Returns list of study sessions
- Pagination with 100 items per page

POST /api/reset_history - Resets all study history data

POST /api/full_reset - Resets entire database to initial state

POST /api/study_sessions/:id/words/:word_id/review - Records a word review result
- Required params: correct



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








