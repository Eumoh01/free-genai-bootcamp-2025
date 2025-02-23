from invoke import task
import sqlite3
import os
import json

DB_PATH = 'words.db'
MIGRATIONS_PATH = 'migrations'
SEEDS_PATH = 'seeds'

@task
def init_db(ctx):
    """Initialize a new SQLite database"""
    if os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} already exists")
        return
    
    # Create empty database file
    open(DB_PATH, 'a').close()
    print(f"Created new database: {DB_PATH}")

@task
def migrate(ctx):
    """Run all pending migrations"""
    # Connect with foreign keys enabled
    conn = sqlite3.connect(DB_PATH + '?foreign_keys=ON')
    cursor = conn.cursor()
    
    # Get list of migration files
    migration_files = sorted([
        f for f in os.listdir(MIGRATIONS_PATH)
        if f.endswith('.sql')
    ])
    
    # Run each migration
    for file_name in migration_files:
        print(f"Running migration: {file_name}")
        file_path = os.path.join(MIGRATIONS_PATH, file_name)
        
        with open(file_path, 'r') as f:
            sql = f.read()
            cursor.executescript(sql)
    
    conn.commit()
    conn.close()
    print("Migrations complete!")

@task
def seed_db(ctx):
    """Import seed data from JSON files"""
    conn = sqlite3.connect(DB_PATH + '?foreign_keys=ON')
    cursor = conn.cursor()

    try:
        # First seed study activities
        activities_file = os.path.join(SEEDS_PATH, 'study_activities.json')
        if os.path.exists(activities_file):
            print("Processing study activities")
            with open(activities_file, 'r') as f:
                activities = json.load(f)
                for activity in activities:
                    cursor.execute("""
                        INSERT INTO study_activities (name, url, preview_url)
                        VALUES (?, ?, ?)
                    """, (activity['name'], activity['url'], activity['preview_url']))
        
        # Dictionary mapping seed files to their group names
        seed_groups = {
            'core_verbs.json': 'Core Verbs',
            'core_nouns.json': 'Core Nouns',
            'basic_phrases.json': 'Basic Phrases'
        }

        # Process word groups
        for seed_file, group_name in seed_groups.items():
            file_path = os.path.join(SEEDS_PATH, seed_file)
            if not os.path.exists(file_path):
                print(f"Warning: Seed file not found: {file_path}")
                continue

            print(f"Processing seed file: {seed_file}")

            # Create group if it doesn't exist
            cursor.execute(
                "INSERT OR IGNORE INTO groups (name) VALUES (?)",
                (group_name,)
            )
            cursor.execute(
                "SELECT id FROM groups WHERE name = ?",
                (group_name,)
            )
            group_id = cursor.fetchone()[0]

            # Read and process words
            with open(file_path, 'r') as f:
                words = json.load(f)
                for word in words:
                    # Insert word
                    cursor.execute("""
                        INSERT INTO words (spanish, pronunciation, english)
                        VALUES (?, ?, ?)
                    """, (word['spanish'], word['pronunciation'], word['english']))
                    word_id = cursor.lastrowid

                    # Link word to group
                    cursor.execute("""
                        INSERT INTO word_groups (word_id, group_id)
                        VALUES (?, ?)
                    """, (word_id, group_id))

            # Update group word count
            cursor.execute("""
                UPDATE groups 
                SET words_count = (
                    SELECT COUNT(*) 
                    FROM word_groups 
                    WHERE group_id = ?
                )
                WHERE id = ?
            """, (group_id, group_id))

        conn.commit()
        print("Seed data import complete!")

    except (sqlite3.Error, json.JSONDecodeError, KeyError) as e:
        conn.rollback()
        print(f"Error seeding database: {str(e)}")
        raise

    finally:
        conn.close()

@task
def reset_db(ctx):
    """Reset database by deleting it and running all migrations"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")
    
    init_db(ctx)
    migrate(ctx)
    seed_db(ctx)
    print("Database reset complete!")
