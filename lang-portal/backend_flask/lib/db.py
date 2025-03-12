from flask import current_app, jsonify, g
import sqlite3

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['SQLITE_DB_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
        
        # Enable foreign key constraints
        cursor = g.db.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        g.db.commit()
        
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app):
    """Register database functions with the Flask app"""
    app.teardown_appcontext(close_db)

def validate_page(page, total_items, per_page=100):
    """Validates page number and returns error response if invalid"""
    if page < 1:
        return jsonify({
            "error": "Invalid page number",
            "message": "Page number must be greater than 0"
        }), 400
    
    total_pages = (total_items + per_page - 1) // per_page
    
    if total_pages > 0 and page > total_pages:
        return jsonify({
            "error": "Page number exceeds available pages",
            "message": f"Page number must not exceed {total_pages}"
        }), 400
    
    return None 