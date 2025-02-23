from flask_sqlalchemy import SQLAlchemy
import sqlite3
from contextlib import contextmanager
from flask import current_app, jsonify

# Create the SQLAlchemy instance
db = SQLAlchemy()

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect('words.db?foreign_keys=ON')
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def validate_page(page, total_items):
    """Validates page number and returns error response if invalid"""
    if page < 1:
        return jsonify({
            "error": "Invalid page number",
            "message": "Page number must be greater than 0"
        }), 400
    
    per_page = current_app.config['ITEMS_PER_PAGE']
    total_pages = (total_items + per_page - 1) // per_page
    
    if total_pages > 0 and page > total_pages:
        return jsonify({
            "error": "Invalid page number",
            "message": f"Page number must not exceed {total_pages}"
        }), 400
    
    return None 