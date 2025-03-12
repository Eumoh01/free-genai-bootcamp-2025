# Frontend Technical Specs

## Goal
- Build the Frontend for a Spanish Language Learning web app 

## Tech Stack
- React
- Typescript
- Tailwind CSS
- Shadcn UI 
- Vite.js


## Global Components
### Sidebar
This is the main navigation menu for the web app. It is used to navigate to different pages. It will be present on all pages.

#### Components
- App name (e.g. "Lang Portal")
- Navigation Links
    - Dashboard
    - Study Activities
    - Words
    - Word Groups
    - Study Sessions
    - Settings

### Breadcrumb
This is a breadcrumb component that will be used to navigate to the current page from the sidebar.

#### Components
- Breadcrumb Item
    - Link to the current page
    - Text of the current page  

## Pages

### Dashboard '/dashboard'
This page provies a summary of the user's learning activity and acts as the default page when the user visits the web app

#### Components
- Last Study Session - Returns details of the most recent study session
    - shows last activity used
    - shows when it was used
    - summarizes the score of the activity
    - Info will be contained in a card
- Study Progress - Returns overall learning progress statistics
    - Total words studied across all study sessions
    - Percentage of words studied across all study sessions
    - Info will be contained in a card
- Quick Stats - Returns summary statistics for study performance
    - Total Study Sessions done
    - Study Streak 
    - Info will be contained in a card

#### API Endpoints
GET /api/dashboard/last_study_session
       
GET /api/dashboard/study_progress
    
GET /api/dashboard/quick_stats


### Study Activities Index '/study_activities'
This page shows all the study activities that is available to the user. The user will be able to select one of the activities to start studying.

#### Components
- Study Activity Card
    - Activity Name

#### API Endpoints
GET /api/study_activities


### Words Index '/words'
This page shows all the words in the database.

#### Components
- Paginated Word List
    - Columns
        - Word in Spanish
            - will be a link to the word details page
        - Word Pronunciation
        - Word Translation in English   
    - Pagination with 100 items per page

#### API Endpoints
GET /api/words

GET /api/words/<id>

### Word Groups Index '/groups'
This page shows all the word groups in the database.

#### Components
- Paginated Word Group List
    - Columns
        - Group Name
        - Number of Words in Group
    - Pagination with 100 items per page

#### API Endpoints
GET /api/groups
GET /api/groups/<id>/words


### Study Sessions Index '/study_sessions'
This page shows all the study sessions that the user has done.

#### Components
- Paginated Study Session List
    - Columns
        - id
        - Activity Name
        - Group Name
        - Start Time
        - End Time
        - Number of Review Items
    - Pagination with 100 items per page

#### API Endpoints
GET /api/study_sessions

### Settings '/settings'
This page shows the settings.

#### Components
- Reset History Button - will delete all the study history data(study sessions and word review items)
- Full Reset Button - will drop all tables an recreate with seed data

#### API Endpoints
POST /api/reset_history

POST /api/full_reset

### Word Details '/words/:id'
This page shows the details of a word.

#### Components
- Word Details Card
    - Word in Spanish
    - Word Pronunciation
- Back to Words Button - will navigate to the words index page

#### API Endpoints
GET /api/words/<id>

GET /api/words






