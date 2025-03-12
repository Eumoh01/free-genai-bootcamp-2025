from flask import jsonify, request
from lib.db import get_db
import sqlite3

def register_routes(app):
    @app.route('/api/reset_history', methods=['POST'])
    def reset_history():
        try:
            with get_db() as db:
                cursor = db.cursor()
                cursor.executescript("""
                    DELETE FROM word_review_items;
                    DELETE FROM study_sessions;
                """)
                db.commit()
                
                return jsonify({
                    "success": True,
                    "message": "Study history cleared"
                })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500
            
    @app.route('/api/full_reset', methods=['POST'])
    def full_reset():
        try:
            with get_db() as db:
                cursor = db.cursor()
                cursor.executescript("""
                    DELETE FROM word_review_items;
                    DELETE FROM study_sessions;
                    DELETE FROM word_groups;
                    DELETE FROM words;
                    DELETE FROM groups;
                """)
                db.commit()
                
                return jsonify({
                    "success": True,
                    "message": "Database reset complete"
                })
        except sqlite3.Error as e:
            return jsonify({
                "error": "Database error",
                "message": str(e)
            }), 500 